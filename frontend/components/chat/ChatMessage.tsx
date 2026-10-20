import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

export function ChatMessage({role,text}:{role:"user"|"assistant";text:string}) {
  return <div className={`agrobot-message agrobot-message-${role}`}>
    <span className="agrobot-message-avatar" aria-hidden="true">{role==="assistant"?<Bot size={15}/>:<User size={14}/>}</span>
    <div className="agrobot-bubble"><span className="sr-only">{role==="assistant"?"AgroBot: ":"Tú: "}</span>
      {role==="assistant"?<ReactMarkdown skipHtml components={{a:({children})=><span>{children}</span>,img:()=>null}}>{text}</ReactMarkdown>:<p>{text}</p>}
    </div>
  </div>;
}
