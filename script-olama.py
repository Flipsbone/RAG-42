import ollama

messages = [
    {'role': 'user', 'content': 'Explique-moi ce qu\'est une API en une phrase.'}
]

# On utilise maintenant le modèle léger "qwen"
stream = ollama.chat(model='qwen', messages=messages, stream=True)

print("AI is typing: ", end="")

for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)