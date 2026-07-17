import { MobileShell } from "@/components/mobile-shell";

export default function CommuterLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MobileShell>{children}</MobileShell>;
}
