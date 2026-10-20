import { streamText, type LanguageModel } from "ai";
import { createChatModel, getChatProviderConfig } from "./chat-provider";
import { z } from "zod";
import { buildChatSystemPrompt, getChatContext } from "./chat-context";

const textPart = z.object({type: z.literal("text"), text: z.string().max(4000)});
const inputMessage = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().trim().min(1).max(4000).optional(),
  parts: z.array(textPart).min(1).max(4).optional(),
}).refine(m => !!m.content || !!m.parts?.some(p => p.text.trim()), "Mensaje vacío");
const payload = z.object({messages: z.array(inputMessage).min(1).max(12)})
  .refine(body => body.messages.at(-1)?.role === "user", "El último mensaje debe ser del usuario");
const errorResponse = (status: number, code: string, message: string) => Response.json({error: {code, message}}, {status, headers: {"Cache-Control": "no-store"}});
type Options = { getModel?: () => LanguageModel; context?: typeof getChatContext; now?: () => number };

export function createChatHandler(options: Options = {}) {
  let windowStart = 0, calls = 0;
  return async function POST(request: Request): Promise<Response> {
    const origin = request.headers.get("origin");
    if (origin && origin !== new URL(request.url).origin) return errorResponse(403,"ORIGIN_NOT_ALLOWED","La solicitud debe proceder de AgroData.");
    if (!request.headers.get("content-type")?.includes("application/json")) return errorResponse(415,"JSON_REQUIRED","Envía un cuerpo JSON.");
    const reader = request.body?.getReader();
    if (!reader) return errorResponse(400,"INVALID_REQUEST","Faltan los mensajes.");
    let text = "", bytes = 0;
    const decoder = new TextDecoder();
    try {
      while (true) {
        const {done,value} = await reader.read(); if (done) break;
        bytes += value.byteLength;
        if (bytes > 32768) { await reader.cancel(); return errorResponse(413,"REQUEST_TOO_LARGE","La conversación supera el límite de tamaño."); }
        text += decoder.decode(value,{stream:true});
      }
      text += decoder.decode();
    } catch { return errorResponse(400,"INVALID_REQUEST","No se pudo leer la conversación."); }
    let body: z.infer<typeof payload>;
    try { body = payload.parse(JSON.parse(text)); }
    catch { return errorResponse(400,"INVALID_MESSAGES","Envía de 1 a 12 mensajes de texto de usuario/asistente, terminando en una pregunta del usuario."); }
    const messages = body.messages.map(m => ({role:m.role,content:m.content ?? m.parts!.map(p=>p.text).join("\n")}));
    if (messages.some(m => m.content.length > 4000) || messages.reduce((n,m) => n+m.content.length,0) > 16000) return errorResponse(413,"CONVERSATION_TOO_LONG","Reduce la longitud de la conversación.");
    const timestamp = (options.now ?? Date.now)();
    if (timestamp-windowStart >= 60000) { windowStart=timestamp; calls=0; }
    if (calls >= 20) return errorResponse(429,"RATE_LIMIT","Hay demasiadas consultas. Inténtalo de nuevo en un minuto.");
    const providerConfig = options.getModel ? null : getChatProviderConfig();
    if (!options.getModel && !providerConfig) return errorResponse(503,"AI_NOT_CONFIGURED","Configura el proveedor y su clave/modelo en frontend/.env.local: AI_PROVIDER=deepseek con DEEPSEEK_API_KEY y DEEPSEEK_MODEL, o AI_PROVIDER=openai con OPENAI_API_KEY y OPENAI_MODEL. Reinicia Next.js.");
    calls++;
    let context: string;
    try { context = await (options.context ?? getChatContext)(messages.filter(m=>m.role==="user").map(m=>m.content).join("\n")); }
    catch { return errorResponse(503,"CONTEXT_UNAVAILABLE","No se pudieron cargar los datos agrícolas. Revisa los archivos JSON del proyecto."); }
    if (context.length > 120000) return errorResponse(422,"CONTEXT_TOO_BROAD","Especifica un cultivo y un departamento para acotar los datos de la consulta.");
    try {
      const model = options.getModel ? options.getModel() : createChatModel(providerConfig!);
      const result = streamText({
        model, system:buildChatSystemPrompt(context), messages,
        maxOutputTokens:900, maxRetries:1, abortSignal:request.signal,
        timeout:60000, onError:()=>undefined,
      });
      return result.toUIMessageStreamResponse({
        headers:{"Cache-Control":"no-store","X-Accel-Buffering":"no"},
        onError:()=>"No se pudo completar la respuesta de AgroBot. Comprueba la configuración del proveedor e inténtalo de nuevo.",
      });
    } catch { return errorResponse(502,"PROVIDER_ERROR","El proveedor de IA no pudo iniciar la respuesta. Inténtalo de nuevo."); }
  };
}
