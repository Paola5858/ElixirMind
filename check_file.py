print('Testing file modification...')
with open('screen_capture.py', 'r') as f:
    content = f.read()
print('File length:', len(content))
lines = content.split('\n')
print('First 20 lines:')
for i, line in enumerate(lines[:20]):
    print(f'{i+1:2}: {line}')
