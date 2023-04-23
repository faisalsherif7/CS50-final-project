// Get the table element
const table = document.querySelector('#untracked-table');

// Add an event listener to the table itself
$(table).on('click', 'button#modify-button', (event) => {
  event.preventDefault();
  const button = event.target;

  // Get the table row containing the clicked button
  const row = button.closest('tr');

  // Store the original row HTML
  const originalRowHTML = row.innerHTML;

  // Get the current date and income values
  const currentDate = row.cells[0].textContent;
  const currentIncome = row.cells[1].textContent;

  // Replace the row's HTML with two input fields and a submit button
  const formHTML = `
    <td><input type="date" class="form-control" name="date" id="date-input" value="${currentDate}"></td>
    <td><input type="text" class="form-control" name="income" id="income-input" value="${currentIncome.replace('$','').replace(',','').replace('.00','')}"></td>
    <td>
      <button class="btn btn-success" type="button" id="save-button">Save</button>
      <button class="btn btn-danger" type="button" id="cancel-button">Cancel</button>
    </td>
  `;
  row.innerHTML = formHTML;

  // Add an event listener to the cancel button to revert the row's content back to the original
  const cancelButton = document.getElementById('cancel-button');
  cancelButton.addEventListener('click', () => {
    row.innerHTML = originalRowHTML;
  });

  // Add an event listener to the save button
  const saveButton = document.getElementById('save-button');
  saveButton.addEventListener('click', () => {
    
    // Get the updated date and income values
    const updatedDate = document.getElementById('date-input').value;
    const updatedIncome = document.getElementById('income-input').value;

    // Send a POST request to the Flask app with the updated values
    $.ajax({
      url: '/update_untracked',
      type: 'POST',
      dataType: 'json',
      data: {
        income_id: button.form.income_id.value,
        date: updatedDate,
        income: updatedIncome
      },
      success: (response) => {
        
        // Refresh the page after
        window.location.reload();

      },
      error: (xhr) => {
        console.log('Error:', xhr.status);
      }
    });
  });
});

// Get the table element
const income_table = document.querySelector('#income-table');

// Add an event listener to the table itself
$(income_table).on('click', 'button#modify-button', (event) => {
  event.preventDefault();
  const button = event.target;

  // Get the table row containing the clicked button
  const row = button.closest('tr');

  // Store the original row HTML
  const originalRowHTML = row.innerHTML;

  // Get the current date and income values
  const currentDate = row.cells[0].textContent;
  const currentIncome = row.cells[1].textContent;

  // Replace the row's HTML with two input fields and a submit button
  const formHTML = `
    <td><input type="date" class="form-control mx-auto" name="date" id="date-input" value="${currentDate}"></td>
    <td><input type="text" class="form-control mx-auto" name="income" id="income-input" value="${currentIncome.replace('$','')}"></td>
    <td>${row.cells[2].textContent}</td>
    <td>${row.cells[3].textContent}</td>
    <td>
      <button class="btn btn-success" type="button" id="save-button">Save</button>
      <button class="btn btn-danger" type="button" id="cancel-button">Cancel</button>
    </td>
  `;
  row.innerHTML = formHTML;

  // Add an event listener to the cancel button to revert the row's content back to the original
  const cancelButton = document.getElementById('cancel-button');
  cancelButton.addEventListener('click', () => {

    // Show rows as before, and show hidden headers
    row.innerHTML = originalRowHTML;

  });

  // Add an event listener to the save button
  const saveButton = document.getElementById('save-button');
  saveButton.addEventListener('click', () => {
    
    // Get the updated date and income values
    const updatedDate = document.getElementById('date-input').value;
    const updatedIncome = document.getElementById('income-input').value;

    // Send a POST request to the Flask app with the updated values
    $.ajax({
      url: '/update_income',
      type: 'POST',
      dataType: 'json',
      data: {
        income_id: button.form.income_id.value,
        date: updatedDate,
        income: updatedIncome
      },
      success: (response) => {
        
        // Refresh the page after
        window.location.reload();

      },
      error: (xhr) => {
        console.log('Error:', xhr.status);
      }
    });
  });
});