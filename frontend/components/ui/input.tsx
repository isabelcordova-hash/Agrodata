import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input data-slot="input" className={cn("min-w-0 rounded-md border bg-transparent px-3 py-2 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-50", className)} {...props}/>;
}
