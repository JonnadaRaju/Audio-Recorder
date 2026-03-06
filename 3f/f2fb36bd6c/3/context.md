# Session Context

## User Prompts

### Prompt 1

Two things to fix — one in TSX, one in CSS.

=== FIX 1: Login.tsx and Register.tsx ===
Inside the .auth-left div, find the three .feature-item elements.
Remove the emoji characters (🎙️ 🎥 🤖) from the text content completely.
The text should be plain:
  "High-quality audio recording"
  "Video capture with live preview"
  "AI assistant for your recordings"
The CSS ::before dot will handle the icon.

=== FIX 2: Auth.css ===

Fix the vertical spacing so content fills the full left panel height:

....

