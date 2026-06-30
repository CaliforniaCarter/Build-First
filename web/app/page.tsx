import Link from "next/link";
import { MarketingBg } from "@/components/MarketingBg";
import styles from "./page.module.css";

// The Tenex front door. Minimal: a hero + one CTA into onboarding. No marketing wall.
export default function MarketingPage() {
  return (
    <>
      <MarketingBg />

      <div className={styles.page}>
        <div className="wrap">
          {/* nav */}
          <nav className={styles.nav}>
            <div className={styles.navbar}>
              <div className="brand">
                <span className="word">
                  timbre<span className="dot">.</span>
                </span>
                <span className={styles.fortenex}>for tenex</span>
              </div>
              <div className={styles.navcta}>
                <Link className={styles.openapp} href="/home">
                  open timbre →
                </Link>
                <Link className={styles.navbtn} href="/onboarding/why">
                  get started <span className={styles.ar}>→</span>
                </Link>
              </div>
            </div>
          </nav>

          {/* hero */}
          <section className={styles.hero}>
            <div>
              <span className="eyebrow mb-[22px]">built for the creator cup</span>
              <h1 className={`serif ${styles.h1}`}>
                you do the work.
                <br />
                <span className="hl">timbre writes the post.</span>
              </h1>
              <p className={styles.hsub}>
                you already ship things worth posting. timbre turns what you actually did into a
                post in your voice, with the receipts. you approve every one — it never posts for
                you.
              </p>
              <div className={styles.hctas}>
                <Link className={styles.big} href="/onboarding/why">
                  find your voice <span className={styles.ar}>→</span>
                </Link>
              </div>
              <div className={styles.trust}>
                <span className={styles.pip} /> from zero · first post in under 10 minutes · stays on
                your machine · drafts only
              </div>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
