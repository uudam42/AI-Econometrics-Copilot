import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost";

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-accent text-white hover:bg-blue-800 disabled:bg-stone-300",
  secondary:
    "bg-white text-foreground border border-border hover:bg-stone-50 disabled:text-stone-400",
  ghost: "text-foreground hover:bg-stone-100 disabled:text-stone-400",
};

export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }
>(({ className, variant = "primary", ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed",
      variantClasses[variant],
      className
    )}
    {...props}
  />
));
Button.displayName = "Button";
