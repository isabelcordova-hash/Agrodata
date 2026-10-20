"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Bot, ChevronRight, MessageCircle, RotateCcw, Sprout, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Card } from "../ui/card";
import { ScrollArea } from "../ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

const suggestions=["¿Cuál es el mejor distrito para PAPA?","¿Qué tan preciso es el modelo?","¿Cuál es la proyección para 2027?"];
const transport=new DefaultChatTransport({
  api:"/api/chat",
  fetch:async(input,init)=>{
    const response=await fetch(input,init);
    if(!response.ok){
      let message="No se pudo conectar con AgroBot. Inténtalo de nuevo.";
      try{
        const data=await response.json();
        message=data.error?.code==="AI_NOT_CONFIGURED"
          ?"AgroBot aún no está configurado. Para DeepSeek, configura AI_PROVIDER=deepseek, DEEPSEEK_API_KEY y DEEPSEEK_MODEL en frontend/.env.local y reinicia Next.js. Para OpenAI, usa AI_PROVIDER=openai, OPENAI_API_KEY y OPENAI_MODEL."
          :data.error?.message||message;
      }catch{/* Preserve a readable fallback for non-JSON server errors. */}
      throw new Error(message);
    }
    return response;
  },
  prepareSendMessagesRequest:({messages})=>{
    let length=0;
    const recent=[];
    for(const message of [...messages].reverse()){
      const content=message.parts.filter(part=>part.type==="text").map(part=>part.text).join("\n");
      if(!content.trim()||(message.role!=="user"&&message.role!=="assistant"))continue;
      if(recent.length>=11||length+content.length>16000)break;
      recent.unshift({role:message.role,content});length+=content.length;
    }
    return {body:{messages:recent}};
  },
});

export function ChatWidget(){
  const [open,setOpen]=useState(false);
  const trigger=useRef<HTMLButtonElement>(null),bottom=useRef<HTMLDivElement>(null);
  const reduceMotion=useReducedMotion();
  const {messages,sendMessage,status,error,clearError,setMessages,stop,regenerate}=useChat({transport});
  const busy=status==="submitted"||status==="streaming";
  useEffect(()=>{if(open)bottom.current?.scrollIntoView({block:"nearest",behavior:"instant"})},[messages,status,open]);
  const close=()=>{setOpen(false);trigger.current?.focus()};
  const send=(text:string)=>{if(busy)return;clearError();void sendMessage({text}).catch(()=>{})};

  return <div className="agrobot-widget">
    <AnimatePresence>
      {open&&<motion.div className="agrobot-window" initial={reduceMotion?false:{opacity:0,y:16,scale:.97}} animate={{opacity:1,y:0,scale:1}} exit={{opacity:0,y:10,scale:.97}} transition={{duration:reduceMotion?0:.18}}>
        <Card className="agrobot-card" role="dialog" aria-labelledby="agrobot-title" aria-describedby="agrobot-description" onKeyDown={event=>{if(event.key==="Escape"){event.stopPropagation();close()}}}>
          <header className="agrobot-header"><span className="agrobot-brand-icon"><Bot size={23}/></span><div><h2 id="agrobot-title">AgroBot Asistente <span/></h2><p id="agrobot-description">Rendimientos, cultivos y proyecciones.</p></div><div className="agrobot-tools"><button type="button" title="Nueva conversación" aria-label="Nueva conversación" disabled={busy||!messages.length} onClick={()=>{clearError();setMessages([])}}><RotateCcw size={16}/></button><button type="button" aria-label="Cerrar AgroBot" onClick={close}><X size={19}/></button></div></header>
          <ScrollArea className="agrobot-messages" aria-label="Conversación con AgroBot">
            {!messages.length&&<section className="agrobot-welcome"><span className="agrobot-welcome-icon"><Sprout size={29}/></span><span className="agrobot-eyebrow">INTELIGENCIA PARA TU TERRITORIO</span><h3>Una pregunta.<br/>Una nueva perspectiva.</h3><p>Soy AgroBot. Te ayudo a explorar los datos de AgroData. ¿Por dónde empezamos?</p><div className="agrobot-suggestions">{suggestions.map(question=><button type="button" key={question} disabled={busy} onClick={()=>send(question)}>{question}<ChevronRight size={14}/></button>)}</div></section>}
            <div role="log" aria-label="Mensajes de la conversación" aria-live="polite" aria-relevant="additions text">
              {messages.map(message=>{
                const text=message.parts.filter(part=>part.type==="text").map(part=>part.text).join("\n");
                return text&&(message.role==="user"||message.role==="assistant")?<ChatMessage key={message.id} role={message.role} text={text}/>:null;
              })}
            </div>
            {busy&&<div className="agrobot-typing" role="status"><Bot size={15}/><span/><span/><span/><small>{status==="submitted"?"Consultando los datos…":"AgroBot está respondiendo…"}</small></div>}
            {error&&<div className="agrobot-error" role="alert"><strong>No se pudo completar la consulta</strong><p>{error.message}</p><button type="button" onClick={()=>{clearError();void regenerate().catch(()=>{})}}>Volver a intentar</button></div>}
            <div ref={bottom}/>
          </ScrollArea>
          <footer className="agrobot-footer"><ChatInput busy={busy} onSend={send} onStop={()=>{void stop()}}/><p>Basado en datos de AgroData. Verifica las cifras importantes.</p></footer>
        </Card>
      </motion.div>}
    </AnimatePresence>
    <button ref={trigger} type="button" className="agrobot-launcher" aria-label={open?"Cerrar AgroBot":"Abrir AgroBot"} aria-expanded={open} aria-haspopup="dialog" onClick={()=>open?close():setOpen(true)}>{open?<X size={23}/>:<MessageCircle size={25}/>}<span className="agrobot-launcher-dot"/><span className="agrobot-launcher-label">Pregúntale a AgroBot</span></button>
  </div>;
}
