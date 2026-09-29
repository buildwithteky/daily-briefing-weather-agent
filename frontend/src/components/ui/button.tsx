import { Button as ButtonPrimitive } from "@base-ui/react/button";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/* Design system: 4px radius, DM Mono Medium, ALL CAPS, letter-spacing 0.
   Hover keeps the background colour and only adds a soft shadow. */
const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-1.5 whitespace-nowrap rounded-[4px] border border-transparent font-mono text-xs font-medium uppercase tracking-[0] transition-shadow outline-none select-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 hover:shadow-[0_4px_12px_rgba(38,37,37,0.18)] [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-[#F9632D] text-white",
        secondary: "bg-[#262525] text-white",
        white: "bg-white text-[#262525] border-[#d9d5d0]",
        outline: "bg-white text-[#262525] border-[#d9d5d0]",
        ghost: "bg-transparent text-[#262525] hover:shadow-none hover:underline",
        destructive: "bg-[#c62828] text-white",
        link: "text-[#262525] underline underline-offset-4 hover:shadow-none",
      },
      size: {
        default: "h-9 px-3.5",
        xs: "h-7 px-2.5 text-[11px]",
        sm: "h-8 px-3",
        lg: "h-11 px-5 text-sm",
        icon: "size-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}

export { Button, buttonVariants };
