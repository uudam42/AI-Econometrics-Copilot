import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "neutral" | "info" | "warning" | "danger" | "success";

const variantClasses: Record<BadgeVariant, string> = {
  neutral: "bg-stone-100 text-stone-700 border-stone-200",
  info: "bg-blue-50 text-blue-700 border-blue-200",
  warning: "bg-amber-50 text-amber-800 border-amber-200",
  danger: "bg-red-50 text-red-700 border-red-200",
  success: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

export function Badge({
  className,
  variant = "neutral",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
}
