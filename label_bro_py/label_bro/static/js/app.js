async function discoverPrinters() {
  try {
    const response = await fetch('/discoverPrinters');
    const data = await response.json();

    if (response.ok) {
      const printerSelect = document.getElementById('printerSelect');
      printerSelect.innerHTML = '<option value="">Select a printer</option>'; // Clear existing options

      data.printers.forEach(printer => {
        const option = document.createElement('option');
        option.value = printer.identifier;
        option.textContent = printer.identifier;
        printerSelect.appendChild(option);
      });

      logResponse('Printers discovered successfully.');
    } else {
      logResponse(`Error: ${data.error}`);
    }
  } catch (error) {
    logResponse(`Error: ${error.message}`);
  }
}

const API_ENDPOINT = '/previewLabels';
const DEBOUNCE_DELAY = 2000;

// Main initialization function
function init() {
  logResponse("initializing all the junk");
  setupLabelTextAreaListener();
}

// Set up event listener with debounce for textarea input
function setupLabelTextAreaListener() {
  let debounceTimeout;
  const labelTextArea = document.getElementById('labelText');
  labelTextArea.addEventListener('input', () => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      const labelText = labelTextArea.value;
      previewLabels(labelText);
    }, DEBOUNCE_DELAY);
  });
}

function handleResponse(response) {
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

// Fetch label previews from the server
async function fetchLabelPreviews(labelText) {
  logResponse("fetching label previews");
  try {
    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        data: {
          text: labelText,
          shouldPrintFullLabel: document.getElementById('printFullLabel').checked,
          shouldPrintSmallLabel: document.getElementById('printSmallLabel').checked,
        }
      })
    });

    const data = await handleResponse(response);
    return data;
  } catch (error) {
    logResponse(`Error: ${error.message}`);
    return null;
  }
}

// Preview labels by updating the DOM
async function previewLabels(labelText) {
  const data = await fetchLabelPreviews(labelText);

  if (data && !data.error) {
    clearPreviews();
    updatePreviews(data, labelText);
  } else if (data && data.error) {
    handleError(new Error(data.error));
  }
}

// Clear previous label previews from the DOM
function clearPreviews() {
  const previewsContainer = document.getElementById('labelPreviews');
  previewsContainer.innerHTML = '';
}

// Update the DOM with new label previews
function updatePreviews(data, labelText) {
  const lines = labelText.split('\n');
  lines.forEach((line, index) => {
    if (line.trim()) {
      const fullLabel = data.full_labels[index] || '';
      const smallLabel = data.small_labels[index] || '';

      // if (!fullLabel || !smallLabel) {
      //   handleError(new Error(`Label data missing for line ${index + 1}`));
      //   return;
      // }

      const labelPair = createLabelPairElement(index, fullLabel, smallLabel);
      const previewsContainer = document.getElementById('labelPreviews');
      previewsContainer.appendChild(labelPair);
    }
  });
}

// Create a DOM element for a pair of label previews
function createLabelPairElement(index, fullLabel, smallLabel) {
  const labelPair = document.createElement('div');
  labelPair.className = 'label-pair';

  const lineHeader = document.createElement('h6');
  lineHeader.textContent = `Label ${index + 1}`;

  const fullLabelImg = document.createElement('img');
  fullLabelImg.src = fullLabel;
  fullLabelImg.alt = fullLabel ? 'Full Label Preview' : 'N/A';
  fullLabelImg.className = 'full-label';

  const smallLabelImg = document.createElement('img');
  smallLabelImg.src = smallLabel;
  smallLabelImg.alt = smallLabel ? 'Small Label Preview' : 'N/A';
  smallLabelImg.className = 'small-label';

  labelPair.appendChild(lineHeader);
  labelPair.appendChild(fullLabelImg);
  labelPair.appendChild(smallLabelImg);

  return labelPair;
}

// Handle and display errors
function handleError(error) {
  const errorMessage = error.message || 'An unknown error occurred';
  logResponse(`Error: ${errorMessage}`);
  document.getElementById('waiting').innerText = '!!! ERROR !!!';
}

function logResponse(text) {
  const timestamp = new Date().toLocaleString();
  const responseContainer = document.getElementById('response');
  if (responseContainer) {
    const responseDiv = document.createElement('div');
    responseDiv.textContent = `${timestamp}: ${text}`;
    responseContainer.prepend(responseDiv);
  }
}

function printAIGeneratedImage() {
  const ditheredImageElement = document.querySelector('.dithered-image');
  if (ditheredImageElement) {
    const imageData = ditheredImageElement.src.split(',')[1]; // Extract base64 data
    fetch('/printImage', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ image_data: imageData })
    })
      .then(response => response.json())
      .then(data => {
        if (data.status) {
          logResponse(data.status);
        } else if (data.error) {
          const errorMessage = data.filename && data.line_number
            ? `${data.filename}:${data.line_number}: ${data.error}`
            : `Error: ${data.error}`;
          logResponse(errorMessage);
        }
      })
      .catch(error => {
        const errorMessage = error.filename && error.line_number
          ? `${error.filename}:${error.line_number}: ${error.message}`
          : `Error: ${error.message}`;
        logResponse(errorMessage);
      });
  } else {
    logResponse('No dithered image available to print.');
  }
}


function printLabels() {
  const labelText = document.getElementById('labelText').value;
  const shouldPrintFullLabel = document.getElementById('printFullLabel').checked
  const shouldPrintSmallLabel = document.getElementById('printSmallLabel').checked

  logResponse(`printing labels.  print full: ${shouldPrintFullLabel}, print small: ${shouldPrintSmallLabel}`);

  document.getElementById('waiting').innerText = "Waiting for response..."

  fetch('/printLabels', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      data: {
        text: labelText,
        shouldPrintFullLabel: shouldPrintFullLabel,
        shouldPrintSmallLabel: shouldPrintSmallLabel,
      }
    })
  })
    .then(response => response.json())
    .then(data => {
      document.getElementById('waiting').innerText = '';

      logResponse(`${JSON.stringify(data, null, 2)}`);
    })
    .catch(handleError);
}

async function submitAIText() {
  const aiText = document.getElementById('aiText').value.trim();
  if (!aiText) {
    alert('Please enter a prompt before submitting.');
    return;
  }

  logResponse(`Prompt submitted.  Awaiting response from OpenAI...`);

  const response = await fetch('/aiGenerate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ prompt: aiText })
  });

  const data = await response.json();

  if (!response.ok) {
    logResponse(`Error: ${data.error || 'Unknown error'}`);
    if (data.details) {
      logResponse(`Details: ${data.details}`);
    }
    console.log("ERROROROROR!!!")
    console.log(response)

    console.log(response.body);

    //# Handle 400 response code
    // const data = error.response ? await error.response.json() : {};
    logResponse(`Error: ${error.message}`);
    if (data && data.details) {
      logResponse(`Details: ${data.details}`);
    }
    if (data && data.response) {
      logResponse(`Response: ${data.response}`);
    }
  }


  if (data.image && data.dithered_image) {
    updatePreviewWithGeneratedImage(data.image, data.dithered_image);
  }

  if (data.error) {
    logResponse(`Error: ${data.error}`);
  }

  if (data.details) {
    logResponse(`Details: ${data.details}`);
  }

  if (data.code) {
    const apiResponseLog = document.getElementById('apiResponseLog');
    const responseDiv = document.createElement('pre');
    responseDiv.className = 'language-python';
    const codeElement = document.createElement('code');
    codeElement.className = 'language-python';
    codeElement.textContent = data.code;
    responseDiv.appendChild(codeElement);
    apiResponseLog.prepend(responseDiv);

    // Highlight the code using Prism.js
    Prism.highlightElement(codeElement);

    generatedCode = data.code;
    logResponse(`AI Generated Code: ${data.code}`);
  }


}

let generatedCode = '';

// Function to execute the generated code
async function executeGeneratedCode() {
  if (!generatedCode) {
    logResponse('No code to execute. Please generate code first.');
    return;
  }

  try {
    logResponse('Executing generated code...');
    const response = await fetch('/executeCode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code: generatedCode })
    });

    const data = await response.json();

    if (!response.ok) {
      logResponse(`Error: ${data.error || 'Unknown error'}`);
      if (data.details) {
        logResponse(`Details: ${data.details}`);
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    if (data.error) {
      logResponse(`Error: ${data.error}`);
    }
    if (data.details) {
      logResponse(`Details: ${data.details}`);
    }
    if (data.status) {
      logResponse(data.status);
    }
  } catch (error) {
    logResponse(`Execution error: ${error.message}`);
  }
}

function updatePreviewWithGeneratedImage(imageData, ditheredImageData) {
  const previewsContainer = document.getElementById('labelPreviews');
  previewsContainer.innerHTML = ''; // Clear previous previews

  const originalImgElement = document.createElement('img');
  originalImgElement.src = imageData;
  originalImgElement.alt = 'Original Image Preview';
  originalImgElement.className = 'original-image';

  const ditheredImgElement = document.createElement('img');
  ditheredImgElement.src = ditheredImageData;
  ditheredImgElement.alt = 'Dithered Image Preview';
  ditheredImgElement.className = 'dithered-image';

  const imagePair = document.createElement('div');
  imagePair.className = 'image-pair';
  imagePair.appendChild(originalImgElement);
  imagePair.appendChild(ditheredImgElement);

  previewsContainer.appendChild(imagePair);
}

function openTab(evt, tabName) {
  // Declare all variables
  var i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

// Initialize the first tab as active
document.addEventListener('DOMContentLoaded', (event) => {
  document.querySelector('.nav-link').click();
  init();
});
