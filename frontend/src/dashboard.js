document.addEventListener("DOMContentLoaded", async () => {
  // ---- username fetch ----
  try {
    const res = await fetch("/api/current_user");
    if (res.status === 401) {
      window.location.href = "/login.html";
      return;
    }
    const data = await res.json();
    document.getElementById("sidebar-username").textContent = data.fullname;
    document.getElementById("user-first-name").textContent =
      data.fullname.split(" ")[0].toUpperCase();
  } catch (err) {
    console.error("Failed to load user info:", err);
  }

  const monthNames = ["January","February","March","April","May","June",
    "July","August","September","October","November","December"];

  let today = new Date();
  let viewYear = today.getFullYear();
  let viewMonth = today.getMonth();

  function renderCalendar(year, month) {
    const table = document.getElementById('cal-table');
    const label = document.getElementById('cal-month-label');

    table.querySelectorAll('tr:not(:first-child)').forEach(row => row.remove());
    label.textContent = `${monthNames[month]} ${year}`;

    const firstDay = new Date(year, month, 1);
    let startOffset = (firstDay.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    let date = 1;
    for (let row = 0; row < 6 && date <= daysInMonth; row++) {
      const tr = document.createElement('tr');
      for (let col = 0; col < 7; col++) {
        const td = document.createElement('td');
        if (row === 0 && col < startOffset) {
          td.textContent = '';
        } else if (date > daysInMonth) {
          td.textContent = '';
        } else {
          td.textContent = date;
          const isToday = date === today.getDate() &&
                           month === today.getMonth() &&
                           year === today.getFullYear();
          if (isToday) td.classList.add('active');
          date++;
        }
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
  }

  document.getElementById('cal-prev').addEventListener('click', () => {
    viewMonth--;
    if (viewMonth < 0) { viewMonth = 11; viewYear--; }
    renderCalendar(viewYear, viewMonth);
  });

  document.getElementById('cal-next').addEventListener('click', () => {
    viewMonth++;
    if (viewMonth > 11) { viewMonth = 0; viewYear++; }
    renderCalendar(viewYear, viewMonth);
  });

  renderCalendar(viewYear, viewMonth);

  document.getElementById("logout-Btn").addEventListener('click', function(){
    fetch("/logout", {method:"POST"})
        .then(function(response){
            return response.json();
        })
        .then(function(data){
            if(data.status === "success"){
                window.location.href = "/login.html";
            }
        })
  });
});