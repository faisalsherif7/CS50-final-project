// Get all the 'Modify' buttons in the table
const modifyButtons = document.querySelectorAll('#modify-form button[type="submit"]');


// Add an event listener to each 'Modify' button
modifyButtons.forEach((button) => {
  button.addEventListener('click', (event) => {
    event.preventDefault();
    
    // Get the table row containing the clicked button
    const row = button.closest('tr');

    // Store the original row HTML
    const originalRowHTML = row.innerHTML;
    
    // Get the current date and income values
    const currentDate = row.cells[0].textContent;
    const currentIncome = row.cells[1].textContent;
    
    // Replace the row's HTML with a form containing two input fields and a submit button
    const formHTML = `
    <form id="update-form" action="/update_income" method="post">
        <input type="hidden" name="income_id" value="${button.form.income_id.value}">
        <td><input type="date" class="form-control" name="date" id="date-input" value="${currentDate}"></td>
        <td><input type="text" class="form-control" name="income" id="income-input" value="${currentIncome}"></td>
        <td>
        <button class="btn btn-success" type="submit">Save</button>
        <button class="btn btn-danger" type="button" id="cancel-button">Cancel</button>
        </td>
    </form>
    `;

    // Replace the row's content with the form
    row.innerHTML = formHTML;

    // Add an event listener to the cancel button to revert the row's content back to the original
    const cancelButton = document.getElementById('cancel-button');
    cancelButton.addEventListener('click', () => {
    row.innerHTML = originalRowHTML;
    });
    
    // Add an event listener to the form's submit button
    const updateForm = document.getElementById('update-form');
    updateForm.addEventListener('submit', (event) => {
      event.preventDefault();
      
      // Get the updated date and income values
      const updatedDate = document.getElementById('date-input').value;
      const updatedIncome = document.getElementById('income-input').value;
      
      // Send a POST request to the Flask app with the updated values
      const fetchOptions = {
        method: 'POST',
        body: new FormData(updateForm)
      };
      fetch('/update_entry', fetchOptions)
        .then((response) => response.json())
        .then((data) => {
          // Redirect back to the same page
          window.location.href = window.location.href;
        });
    });
  });
});
