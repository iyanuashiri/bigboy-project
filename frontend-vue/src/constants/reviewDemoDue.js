/**
 * Shown on the Review queue only when the server returns no due rows — same layout as real cards.
 * `bite` uses demo-* ids so grading stays client-side until real reviews exist.
 */

export const REVIEW_DEMO_DUE = [
  {
    id: 'demo-review-1',
    bite: 'demo-bite-1',
    subject_id: 0,
    subject_name: 'Cognitive psychology (self-paced)',
    topic_id: 0,
    topic_name: 'Working memory limits',
    bite_name: 'The magic number seven (give or take two)',
    bite_body:
      'Miller’s classic framing: people can hold roughly seven meaningful chunks in working memory, though the exact count depends on task and chunking strategy. Why does chunking increase apparent capacity without changing the underlying limit?',
    is_locked: false,
    interval_days: 1,
    repetitions: 0,
    next_review_at: new Date().toISOString(),
    last_grade: '',
  },
  {
    id: 'demo-review-2',
    bite: 'demo-bite-2',
    subject_id: 0,
    subject_name: 'Cognitive psychology (self-paced)',
    topic_id: 0,
    topic_name: 'Encoding variability',
    bite_name: 'Same idea, different contexts',
    bite_body:
      'Studying the same material in varied settings can strengthen retrieval cues later. When would you *not* want variability during first learning?',
    is_locked: false,
    interval_days: 2,
    repetitions: 1,
    next_review_at: new Date().toISOString(),
    last_grade: 'good',
  },
  {
    id: 'demo-review-3',
    bite: 'demo-bite-3',
    subject_id: 0,
    subject_name: 'Technical writing',
    topic_id: 0,
    topic_name: 'Plain structure',
    bite_name: 'Lead with the decision',
    bite_body:
      'Busy readers scan for outcomes first. Put the recommendation (or answer) before the evidence chain. Rewrite: “We should delay the launch because…” vs burying the conclusion in paragraph three.',
    is_locked: false,
    interval_days: 1,
    repetitions: 0,
    next_review_at: new Date().toISOString(),
    last_grade: '',
  },
]

export function isDemoReviewBite(biteId) {
  return String(biteId).startsWith('demo-bite-')
}
