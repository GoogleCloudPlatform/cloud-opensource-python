(function ($) {
  // USE STRICT
  "use strict";

  try {
    // Percent Chart
    var doughnutChart = document.getElementById("percent-chart-compatibility");
    var num_success = doughnutChart.getAttribute("data-success");
    var num_conflict = doughnutChart.getAttribute("data-conflict");
    doughnutChart.height = 280;
    new Chart(doughnutChart, {
        type: 'doughnut',
        data: {
          datasets: [
            {
              label: "Compatibility Status",
              data: [num_success, num_conflict],
              backgroundColor: [
                '#00b5e9',
                '#fa4251'
              ],
              hoverBackgroundColor: [
                '#00b5e9',
                '#fa4251'
              ],
              borderWidth: [
                0, 0
              ],
              hoverBorderColor: [
                'transparent',
                'transparent'
              ]
            }
          ],
          labels: [
            'Success',
            'Having Conflicts'
          ]
        },
        options: {
          maintainAspectRatio: false,
          responsive: true,
          cutoutPercentage: 55,
          animation: {
            animateScale: true,
            animateRotate: true
          },
          legend: {
            display: false
          },
          tooltips: {
            titleFontFamily: "Poppins",
            xPadding: 15,
            yPadding: 10,
            caretPadding: 0,
            bodyFontSize: 16
          }
        }
    });

  } catch (error) {
    console.log(error);
  }

})(jQuery);

(function ($) {
  // USE STRICT
  "use strict";

  try {
    // Percent Chart
    var doughnutChart = document.getElementById("percent-chart-dependency");
    var num_success = doughnutChart.getAttribute("data-success");
    var num_deprecated = doughnutChart.getAttribute("data-deprecated");
    var num_outdated = doughnutChart.getAttribute("data-outdated");
    doughnutChart.height = 280;
    new Chart(doughnutChart, {
        type: 'doughnut',
        data: {
          datasets: [
            {
              label: "Compatibility Status",
              data: [num_success, num_deprecated, num_outdated],
              backgroundColor: [
                '#00b5e9',
                '#fa4251',
                '#f1c40f'
              ],
              hoverBackgroundColor: [
                '#00b5e9',
                '#fa4251',
                '#f1c40f'
              ],
              borderWidth: [
                0, 0, 0
              ],
              hoverBorderColor: [
                'transparent',
                'transparent',
                'transparent'
              ]
            }
          ],
          labels: [
            'Success',
            'Deprecated Dependency',
            'Outdated Dependency'
          ]
        },
        options: {
          maintainAspectRatio: false,
          responsive: true,
          cutoutPercentage: 55,
          animation: {
            animateScale: true,
            animateRotate: true
          },
          legend: {
            display: false
          },
          tooltips: {
            titleFontFamily: "Poppins",
            xPadding: 15,
            yPadding: 10,
            caretPadding: 0,
            bodyFontSize: 16
          }
        }
    });

  } catch (error) {
    console.log(error);
  }

})(jQuery);

// Sort the table rows by the details column to display the packages having
// issues first.
(function ($) {
    var table = document.getElementById("package-details");
    switching = true;
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
          shouldSwitch = false;
          x = rows[i].getElementsByTagName("TD")[3];
          y = rows[i + 1].getElementsByTagName("TD")[3];
          if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
            shouldSwitch = true;
            break;
          }
        }
        if (shouldSwitch) {
          rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
          switching = true;
        }
    }
})(jQuery);

(function ($) {
    // USE STRICT
    "use strict";
    $(".animsition").animsition({
      inClass: 'fade-in',
      outClass: 'fade-out',
      inDuration: 900,
      outDuration: 900,
      linkElement: 'a:not([target="_blank"]):not([href^="#"]):not([class^="chosen-single"])',
      loading: true,
      loadingParentElement: 'html',
      loadingClass: 'page-loader',
      loadingInner: '<div class="page-loader__spin"></div>',
      timeout: false,
      timeoutCountdown: 5000,
      onLoadEvent: true,
      browser: ['animation-duration', '-webkit-animation-duration'],
      overlay: false,
      overlayClass: 'animsition-overlay-slide',
      overlayParentElement: 'html',
      transition: function (url) {
        window.location.href = url;
      }
    });

})(jQuery);
