import Link from "next/link";
import { MarketingBg } from "@/components/MarketingBg";
import styles from "./page.module.css";

// The Tenex internal front door. Static marketing landing; the only animated
// (client) part is <MarketingBg/>, so the page itself stays a server component.
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
                you already ship things worth posting. timbre turns what you actually did into your
                voice — receipts and all — so showing up takes minutes, not your whole afternoon.
              </p>
              <div className={styles.hctas}>
                <Link className={styles.big} href="/onboarding/why">
                  find your voice <span className={styles.ar}>→</span>
                </Link>
                <Link className={styles.quiet} href="#map">
                  ↓ is this you?
                </Link>
              </div>
              <div className={styles.trust}>
                <span className={styles.pip} /> from zero · first post in under 10 minutes · stays on
                your machine
              </div>
            </div>

            {/* floating product card — marketing illustration */}
            <div className={styles.pcard}>
              <div className={styles.pch}>
                <span className={styles.pchL}>
                  <span className={styles.pchPip} /> your work, captured → a post
                </span>
                <span className={styles.ev}>8.6 ✓</span>
              </div>
              <div className={styles.post}>
                <div className={styles.ph}>
                  <span className={styles.av}>C</span>
                  <span>
                    <span className={styles.nm}>carter chasson</span>
                    <br />
                    <span className={styles.mt}>draft · in your voice</span>
                  </span>
                </div>
                <div className={styles.pbody}>
                  {`shipped timbre's onboarding today. no meetings, no deck — just built it and watched it work. honestly the fastest i've moved in months.`}
                </div>
                <div className={styles.rc}>
                  <span className="chiprc">
                    <span className="ic">▤</span> onboarding.diff
                  </span>
                  <span className="chiprc">
                    <span className="ic">▶</span> demo.gif
                  </span>
                  <span className="chiprc">
                    <span className="ic">⌁</span> transcript
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* problem → goal map */}
          <section className={styles.map} id="map">
            <h2 className={`serif ${styles.mapH2}`}>if any of this is you—</h2>
            <div className={styles.mh}>
              timbre is built for the builders, not the content people. pick what stings.
            </div>
            <div className={styles.rows}>
              <div className={styles.pg}>
                <div className={styles.prob}>{`"i ship great work. nobody sees it."`}</div>
                <div className={styles.pgArrow}>
                  <span>so timbre</span>
                  <span className={styles.ln} />
                </div>
                <div className={styles.goal}>
                  ships every post with the <b>proof</b> — the diff, the demo, the real number. the
                  part that&apos;s actually yours.
                </div>
              </div>

              <div className={styles.pg}>
                <div className={styles.prob}>{`"i'm not a 'content person.'"`}</div>
                <div className={styles.pgArrow}>
                  <span>so timbre</span>
                  <span className={styles.ln} />
                </div>
                <div className={styles.goal}>
                  kills the blank page. <b>say what you did</b> — it writes it in your voice, and you
                  just approve.
                </div>
              </div>

              <div className={styles.pg}>
                <div className={styles.prob}>{`"the cup's running and i'm behind."`}</div>
                <div className={styles.pgArrow}>
                  <span>so timbre</span>
                  <span className={styles.ln} />
                </div>
                <div className={styles.goal}>
                  gets you from a <b>cold start to your first in-voice post in under 10 minutes</b>.
                  no corpus, no prep.
                </div>
              </div>

              <div className={styles.pg}>
                <div className={styles.prob}>{`"posting eats my whole afternoon."`}</div>
                <div className={styles.pgArrow}>
                  <span>so timbre</span>
                  <span className={styles.ln} />
                </div>
                <div className={styles.goal}>
                  turns <b>one honest paragraph</b> into a draft you&apos;d actually post. minutes,
                  not hours.
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* footer band */}
        <div className="wrap">
          <div className={styles.band}>
            <div className={styles.bt}>
              runs inside your own <b>claude code</b> &amp; <b>cowork</b> — no account, no login. your
              work never leaves your machine, and timbre <b>never posts for you</b>. drafts only.
            </div>
            <Link className={styles.big} href="/onboarding/why">
              find your voice <span className={styles.ar}>→</span>
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
