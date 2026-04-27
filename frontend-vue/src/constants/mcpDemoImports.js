/** Shown in the UI only when the server returns no imports — reads like saved threads, not scaffolding. */

const T1 = [
  'You: Quick question — when did “vampire rules” get codified in Europe? Garlic, mirrors, running water… feels like a grab bag.',
  'Assistant: A lot of what people repeat today is a mix of Balkan folklore, church polemic, and 19th-century stage fiction. Running water is not a deep medieval constant; it shows up more in later retellings. Mirrors and invitations lean on Victorian novels (Dracula is the big amplifier). Garlic has older roots as a protective charm in several cultures, but it was not universal.',
  'You: So Bram Stoker basically won the branding war.',
  'Assistant: Stoker plus theater and early film. His Count is aristocratic, foreign, and strangely modern — that template displaced many older “revenant” stories where the undead were peasants, localized, and dealt with by community ritual rather than lone heroes.',
  'You: What about werewolves — same kind of drift?',
  'Assistant: Similar pattern: trial records and church commentary in medieval France/Germany describe wolf attacks and “lycanthropy” in ways that blur mental illness, political accusation, and legend. The full moon rule is largely modern popularization; older tales tied transformation to belts, ointments, curses, or seasons.',
  'You: Wild. I started this because a podcast mentioned “strigoi” vs “vampire” and now I’m down a hole.',
  'Assistant: Strigoi (Romanian) overlaps with restless dead who drain vitality; not identical to the Anglo “vampire,” but they fed each other once travel writing and translation circulated the motifs. If you want a clean thread to study next: compare 18th-century vampire panics in Eastern Europe with Enlightenment skeptic pamphlets — it is a neat case study in rumor ecology.',
]

const T2 = [
  'You: Is there any historical basis for silver bullets vs werewolves?',
  'Assistant: Silver as a specific anti-werewolf weapon is mostly modern folklore synthesis — silver bullets show up in fiction more than in early peasant tales. Silver had broader magical associations (purity, moon-metals), which later storytellers mapped onto wolves once werewolves became romantic antiheroes.',
  'You: So the Lone Ranger did not inherit that from medieval peasants.',
  'Assistant: Pretty much. You will find silver in some protective charms, but the “one silver round fixes it” beat is cinematic.',
]

const T3 = [
  'You: Why do vampires keep getting sexier over time?',
  'Assistant: Short version: changing taboos. Early revenant stories are about disgust, boundary violation, and communal hygiene. Gothic fiction eroticizes danger; later media adds consent metaphors, power fantasy, and “immortal grief” as character engines. The monster becomes a mirror for what the audience is willing to flirt with.',
  'You: That tracks with every streaming lineup.',
  'Assistant: If you are building a reading list: Polidori’s “The Vampyre,” Le Fanu’s Carmilla, then Dracula — you can literally watch the motif professionalize across three generations.',
]

function row(id, title, clientLabel, isoDate, lines) {
  const transcript = lines.join('\n')
  return {
    id,
    title,
    client_label: clientLabel,
    raw_payload: null,
    transcript,
    lines,
    status: 'parsed',
    error_message: '',
    created_at: isoDate,
    updated_at: isoDate,
  }
}

export const MCP_DEMO_IMPORTS = [
  row(
    'demo-1',
    'Vampire tropes vs history (Balkan → Victorian)',
    'ChatGPT',
    '2026-04-18T21:14:00.000Z',
    T1,
  ),
  row(
    'demo-2',
    'Silver bullets and werewolf folklore',
    'Claude',
    '2026-04-19T09:02:00.000Z',
    T2,
  ),
  row(
    'demo-3',
    'Why vampires keep getting “sexy” in fiction',
    'ChatGPT',
    '2026-04-20T16:40:00.000Z',
    T3,
  ),
]

const byId = Object.fromEntries(MCP_DEMO_IMPORTS.map((r) => [String(r.id), r]))

export function getMcpDemoImport(importId) {
  return byId[String(importId)] ? { ...byId[String(importId)] } : null
}
