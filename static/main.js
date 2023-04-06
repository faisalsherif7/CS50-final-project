// get all the modify buttons
const modifyButtons = document.querySelectorAll('.modify-btn');

// loop through each modify button and add a click event listener
modifyButtons.forEach((button) => {
  button.addEventListener('click', () => {
    // get the row that contains the clicked button
    const row = button.parentNode.parentNode;
    // get the cells in the row
    const cells = row.cells;

    // loop through each cell and add an input element
    for (let i = 0; i < cells.length - 1; i++) {
      const cell = cells[i];
      const cellValue = cell.innerText;
      cell.innerHTML = `<input type="text" value="${cellValue}" />`;
    }

    // replace the modify button with a save button
    const saveButton = document.createElement('button');
    saveButton.innerText = 'Save';
    saveButton.classList.add('save-btn');
    button.parentNode.replaceChild(saveButton, button);

    // add a click event listener to the save button
    saveButton.addEventListener('click', () => {
      // loop through each cell and replace the input element with its value
      for (let i = 0; i < cells.length - 1; i++) {
        const cell = cells[i];
        const input = cell.firstChild;
        const inputValue = input.value;
        cell.innerHTML = inputValue;
      }

      // replace the save button with the modify button
      const modifyButton = document.createElement('button');
      modifyButton.innerText = 'Modify';
      modifyButton.classList.add('modify-btn');
      saveButton.parentNode.replaceChild(modifyButton, saveButton);
    });
  });
});