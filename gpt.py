import os
import openai

openai.api_key = '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'  # Replace with your OpenAI API key


def process_tex_files(input_dir):
    # Create an output directory to store the corrected files
    output_dir = os.path.join(input_dir, 'corrected')
    os.makedirs(output_dir, exist_ok=True)

    # Get all .tex files from the input directory
    tex_files = [f for f in os.listdir(input_dir) if f.endswith('.tex')]

    # Process each .tex file
    for tex_file in tex_files:
        file_path = os.path.join(input_dir, tex_file)
        output_path = os.path.join(output_dir, tex_file)

        with open(file_path, 'r', encoding='utf-8') as file:
            tex_content = file.read()

        # Make the API call to GPT-3.5 Turbo for spell checking and formatting improvements
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bitte verbessere die Rechtschreibung und das Format des folgenden Latex Dokuments:"},
                {"role": "user", "content": tex_content}
            ],
            max_tokens=4096,
            temperature=0.7,
        )

        corrected_tex_content = response.choices[0].message.content.strip()

        # Write the corrected .tex file to the output directory
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(corrected_tex_content)

        print(f"Processed file: {tex_file}")


def main():
    input_dir = 'output'  # Path to the output directory containing .tex files

    process_tex_files(input_dir)


if __name__ == '__main__':
    main()