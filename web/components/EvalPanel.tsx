"use client";
// The builder-facing eval panel: hides nothing — score, the 6 gates, all 9 dimensions.
// Shared by the compose-final view and the feed post breakdown.
import { useState } from "react";
import { gateLabel, dimLabel } from "@/lib/score";
import type { SerializedScore } from "@/lib/api";
import styles from "./EvalPanel.module.css";

export function EvalPanel({ score }: { score: SerializedScore }) {
  const [showDims, setShowDims] = useState(false);
  const qa = score.quality_avg;
  const barPct = Math.max(0, Math.min(100, (qa / 10) * 100));

  return (
    <aside className={styles.eval}>
      <div className={styles.et}>eval</div>
      <div className={styles.score}>
        <span className={styles.scoren}>{qa.toFixed(1)}</span>
        <span className={styles.scoreo}>/ 10</span>
      </div>
      <div className={styles.ebar}>
        <i style={{ width: `${barPct}%` }} />
      </div>

      <div className={styles.gates}>
        {score.gates.map((g) => (
          <div
            key={g.name}
            className={`${styles.gaterow}${g.passed ? "" : " " + styles.fail}`}
            title={g.reason}
          >
            <span className={styles.gk}>{g.passed ? "✓" : ""}</span>
            {gateLabel(g.name)}
          </div>
        ))}
      </div>

      <button
        className={styles.dimtoggle}
        type="button"
        onClick={() => setShowDims((v) => !v)}
      >
        {showDims ? "hide dimensions ▲" : "show all 9 dimensions ▾"}
      </button>
      {showDims && (
        <div className={styles.dims}>
          {score.dimensions.map((d) => (
            <div key={d.name} className={styles.dim} title={d.reason}>
              <div className={styles.dimhead}>
                <span className={styles.dimlabel}>{dimLabel(d.name)}</span>
                <span className={styles.dimscore}>{d.score.toFixed(1)}/10</span>
              </div>
              <div className={styles.dimbar}>
                <i
                  style={{
                    width: `${Math.max(0, Math.min(100, (d.score / 10) * 100))}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className={styles.gatenote}>
        {score.gates_passed}/{score.gates_total} gates passed. the score is your meter — not a
        gate. edit freely; it re-scores.
      </div>
    </aside>
  );
}
