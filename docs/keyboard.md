# Keyboard Model

`terminalfx` is designed for repeated editing without leaving the keyboard.
Bindings are short, modal only where necessary, and biased toward predictable
list movement.

## Global

| Key | Action |
| --- | --- |
| `q` | Quit the active TUI |
| `:` | Open command palette |
| `tab` | Move focus to next panel |
| `shift+tab` | Move focus to previous panel |
| `o` | Open preview window |

## Source And Routing

| Key | Action |
| --- | --- |
| `m` | Cycle source mode |
| `c` | Cycle camera index when in camera mode |
| `S` | Cycle screen index when in screen mode |
| `w` | Cycle target window when in window mode |
| `p` | Cycle preview mode: `auto`, `ascii`, `pixel` |

## Effect Stack

| Key | Action |
| --- | --- |
| `j` | Select next effect |
| `k` | Select previous effect |
| `J` | Move selected effect down |
| `K` | Move selected effect up |
| `a` | Add effect |
| `x` | Remove selected effect |
| `b` | Toggle selected effect bypass |
| `d` | Duplicate selected effect |
| `n` | Select next look slider |
| `N` | Select previous look slider |
| `[` | Decrease selected look slider |
| `]` | Increase selected look slider |
| `s` | Save effect preset |
| `l` | Load effect preset |

## Transport And Export

| Key | Action |
| --- | --- |
| `space` | Play or pause transport |
| `r` | Toggle realtime record arm |
| `e` | Enqueue export |

## Interaction Rules

- Focus determines which panel receives list-style movement.
- Stack editing acts on the selected effect row.
- Preview mode changes should be visible in both the TUI and preview window.
- Destructive actions should be easy to undo or confirm before permanent export.
