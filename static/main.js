// Get the table element
const table = document.querySelector('#income-table');

// Add an event listener to the table itself
$(table).on('click', 'button[type="submit"]', (event) => {
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
    <td><input type="text" class="form-control" name="income" id="income-input" value="${currentIncome}"></td>
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
      url: '/update_entry',
      type: 'POST',
      dataType: 'json',
      data: {
        income_id: button.form.income_id.value,
        date: updatedDate,
        income: updatedIncome
      },
      success: (response) => {

        // Flash a success message
        $('.alert-success').fadeIn();
        
        // Refresh the page after
        window.location.reload();

      },
      error: (xhr) => {
        console.log('Error:', xhr.status);
      }
    });
  });
});
