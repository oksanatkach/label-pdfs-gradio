from img_outputter_class import ImageOutputter
import gradio as gr
from functools import partial

medical_files_path = 'file_names.txt'
labels_path = 'labelling_results/labels.jsonl'
errors_path = 'labelling_results/errors.jsonl'
skip_path = 'labelling_results/skipped.jsonl'

PDF = ImageOutputter(medical_files_path, labels_path, errors_path, skip_path)

demo = gr.Blocks()
with demo:
    with gr.Row():
        with gr.Column():
            idx, doc, page, doc_image = PDF.get_next()

        with gr.Column():
            class1_btn = gr.Button("Class 1")
            class2_btn = gr.Button("Class 2")
            class3_btn = gr.Button("Class 3")
            class4_btn = gr.Button("Class 4")
            class5_btn = gr.Button("Class 5")
            gr.Textbox('Other actions:')
            dupe_btn = gr.Button("Duplicate")
            empty_btn = gr.Button("Empty")
            skip_page_btn = gr.Button("Skip page")
            skip_file_btn = gr.Button("Skip file")
            with gr.Row():
                prev_page_btn = gr.Button("<")
                next_page_btn = gr.Button(">")

    # classes
    btn_to_class = {
        class1_btn: "class_1",
        class2_btn: "class_2",
        class3_btn: "class_3",
        class4_btn: "class_4",
        class5_btn: "class_5"
    }

    outputs = [idx, doc, page, doc_image]
    for btn in btn_to_class:
        btn.click(fn=partial(PDF.record_label, doc_class=btn_to_class[btn]),
                  outputs=outputs)

    # other actions
    dupe_btn.click(fn=partial(PDF.record_error, error_type='dupe'),
                   outputs=outputs)

    empty_btn.click(fn=partial(PDF.record_error, error_type='empty'),
                    outputs=outputs)

    skip_page_btn.click(fn=PDF.skip_page,
                        outputs=outputs)

    skip_file_btn.click(fn=PDF.skip_file,
                        outputs=outputs)

    prev_page_btn.click(fn=PDF.to_prev_page,
                        outputs=outputs)

    next_page_btn.click(fn=PDF.to_next_page,
                        outputs=outputs)

demo.launch(debug=True, show_error=True, share=True)
