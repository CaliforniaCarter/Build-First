import Link from "next/link";
import { Waveform } from "./Waveform";

export function Brand({ href = "/", bars = 16 }: { href?: string; bars?: number }) {
  return (
    <Link href={href} className="brand">
      <span className="word">
        timbre<span className="dot">.</span>
      </span>
      <Waveform bars={bars} />
    </Link>
  );
}
