import type { ComponentPropsWithoutRef, ElementType, ReactNode } from "react";

type CardProps<T extends ElementType = "div"> = {
  as?: T;
  children: ReactNode;
  className?: string;
} & Omit<ComponentPropsWithoutRef<T>, "as" | "children" | "className">;

function joinClasses(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function Card<T extends ElementType = "div">({
  as,
  children,
  className,
  ...props
}: CardProps<T>) {
  const Component = as ?? "div";

  return (
    <Component
      className={joinClasses(
        "relative z-[var(--layer-card)] rounded-xl border border-[var(--line)] bg-[var(--card)] shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg",
        className,
      )}
      {...props}
    >
      {children}
    </Component>
  );
}