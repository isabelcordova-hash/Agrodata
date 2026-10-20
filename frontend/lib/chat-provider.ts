import { createOpenAI } from "@ai-sdk/openai";

export function getChatProviderConfig() {
  const provider=(process.env.AI_PROVIDER||"openai").trim().toLowerCase();
  if(provider!=="openai"&&provider!=="deepseek")return null;
  const apiKey=(provider==="deepseek"?process.env.DEEPSEEK_API_KEY:process.env.OPENAI_API_KEY)?.trim();
  const model=(provider==="deepseek"?process.env.DEEPSEEK_MODEL||"deepseek-flash":process.env.OPENAI_MODEL)?.trim();
  // Do not send a mistakenly pasted credential as a model identifier.
  if(!apiKey||!model||model.startsWith("sk-"))return null;
  return {provider,apiKey,model,baseURL:provider==="deepseek"?"https://api.deepseek.com/v1":"https://api.openai.com/v1"};
}

export function createChatModel(config: NonNullable<ReturnType<typeof getChatProviderConfig>>) {
  return createOpenAI({apiKey:config.apiKey,baseURL:config.baseURL}).chat(config.model);
}
