from openai import OpenAI


def call_openai_style_model(base_url, api_key, model_name, prompt, **kwargs):
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        **kwargs
    )
    return response.choices[0].message.content
