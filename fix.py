with open('src/ui/components/draggable_list.py', 'r') as f:
    text = f.read()

text = text.replace('def _move_item(self, frame, offset):', '    def _move_item(self, frame, offset):')
text = text.replace('def _on_drag_start(self, event, frame):', '    def _on_drag_start(self, event, frame):')
text = text.replace('def _on_drag_release(self, event):', '    def _on_drag_release(self, event):')

with open('src/ui/components/draggable_list.py', 'w') as f:
    f.write(text)
