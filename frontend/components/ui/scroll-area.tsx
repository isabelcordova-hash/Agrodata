"use client";
import type { ComponentProps } from "react";
import { ScrollArea as Primitive } from "radix-ui";
import { cn } from "@/lib/utils";

export function ScrollArea({className,children,...props}:ComponentProps<typeof Primitive.Root>) {
  return <Primitive.Root className={cn("relative overflow-hidden",className)} {...props}>
    <Primitive.Viewport className="h-full w-full rounded-[inherit]" tabIndex={0}>{children}</Primitive.Viewport>
    <Primitive.Scrollbar orientation="vertical" className="agrobot-scrollbar"><Primitive.Thumb className="agrobot-scroll-thumb"/></Primitive.Scrollbar>
    <Primitive.Corner/>
  </Primitive.Root>;
}
