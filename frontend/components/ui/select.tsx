import * as React from "react";
import { cn } from "@/lib/utils";

export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "block w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground",
      "focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1",
      "disabled:cursor-not-allowed disabled:text-muted",
      className
    )}
    {...props}
  />
));
Select.displayName = "Select";
