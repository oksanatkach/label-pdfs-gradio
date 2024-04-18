# Labelling PDFs with Gradio

Manual labelling with Gradio is not exactly straight-forward.

I have found that Gradio's button output logic does not work well with functions, so I had to rewrite the logic as a class, which is a much neater solution.

There is also a solution here on how to download a PDF into memory and display it in Gradio UI.

### What this app does:
- Downloads PDFs from Azure blob storage
- Displays each page as an image
  *<br/>Note: I tried to display the PDFs as bytes embedded into html, which yields a PDF viewer. However, I have found this fails for some PDFs (displays a blank page). Viewing PDFs as images is much more fail proof.*
- Allows the user to label each page and immediately writes the result into a file
- Allows to skip pages or files and navigate between pages

### Areas for improvement:
- Page navigation logic is buggy
- self.seen logic can be neater and quicker
- Allow to re-label (write to results file with a datetime stamp?)
- Display the current label of a page (and maybe labelling history)
- Allow to filter displayed pages by class for review purposes
- Add unit tests, particularly for page navigation logic
