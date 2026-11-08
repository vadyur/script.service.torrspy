from __future__ import absolute_import

import sys

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'show_overlay_on_pause':
        # src.script тянет vdlib -> requests/urllib3: на SHIELD это секунды, и короткая
        # пауза заканчивалась раньше, чем оверлей был готов.
        from src.overlay import show_overlay_on_pause  # type: ignore
        show_overlay_on_pause(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '')
    else:
        from src.script import main  # type: ignore
        main()
