# Hit The Target

A webcam game you control with your hand. Raise your index finger and touch the moving balls to pop them. You have 60 seconds to score as many points as you can.

Hand tracking uses [MediaPipe Hands](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker), the camera is read with OpenCV, and the game is drawn with [pygame](https://www.pygame.org/).

## How to play

1. While the camera loads, the game shows the rules and the points for each ball. Press **ENTER** once it says *Ready*.
2. Type your name and press **ENTER**.
3. Raise **only your index finger** (keep your other fingers folded). A red cross shows where your fingertip is.
4. Move your fingertip onto the balls to pop them before time runs out.
5. When the game ends, the top 3 scores are shown. Raise your index finger to play again.

### Points

| Target | Points |
| --- | --- |
| 🟠 Orange ball | 1 pt |
| 🟢 Green ball (rare and fast, disappears after 10 seconds) | 10 pts |
| ⭐ Combo: pop 5 balls within 2 seconds | +5 pts |

## Requirements

- Python 3.9 – 3.12 (MediaPipe 0.10 does not support newer versions)
- A webcam

## Installation

```bash
git clone https://github.com/DarkShark02/HitTheTarget.git
cd HitTheTarget

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

## Running

```bash
python main.py
```

High scores are saved locally in `records.txt`.

## Project structure

| File | Description |
| --- | --- |
| `main.py` | The game |
| `generate_sounds.py` | Script that generates `hit.wav`, `combo.wav` and `record.wav` |
| `*.wav` | Sound effects |
| `requirements.txt` | Python dependencies |

## Tips

- Play in a well-lit room with your hand clearly visible to the camera.
- The fingertip position is mapped to the screen with a fixed calibration (`min_x`, `max_x`, `min_y`, `max_y` in `main.py`). If you can't reach some areas of the screen, adjust these values.

## License

Released under the [MIT License](LICENSE) © Flavio Ruggiero.
