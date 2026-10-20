import { Send, Square } from "lucide-react";
import { useRef, useState } from "react";
import { Input } from "../ui/input";
import { Button } from "../ui/button";

export function ChatInput({busy,onSend,onStop}:{busy:boolean;onSend:(text:string)=>void;onStop:()=>void}) {
  const [text,setText]=useState("");
  const composing=useRef(false);
  return <form className="agrobot-input" onSubmit={event=>{
    event.preventDefault();
    if(busy||composing.current||!text.trim())return;
    onSend(text.trim());setText("");
  }}>
    <label htmlFor="agrobot-question" className="sr-only">Tu pregunta para AgroBot</label>
    <Input id="agrobot-question" autoFocus value={text} onChange={event=>setText(event.target.value)} maxLength={2000}
      placeholder="Escribe tu pregunta…" autoComplete="off"
      onCompositionStart={()=>{composing.current=true}} onCompositionEnd={()=>{composing.current=false}}/>
    {busy?<Button type="button" onClick={onStop} className="agrobot-send" aria-label="Detener respuesta"><Square size={15}/></Button>:<Button type="submit" className="agrobot-send" disabled={!text.trim()} aria-label="Enviar pregunta"><Send size={17}/></Button>}
  </form>;
}
