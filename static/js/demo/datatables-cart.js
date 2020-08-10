// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#cartItemTable').DataTable({
      columnDefs: [ {
            targets: [ 0 ],
            orderData: [ 0, 1 ]
        }, {
            targets: [ 1 ],
            orderData: [ 1, 0 ]
        }, {
            targets: [ 3 ],
            orderData: [ 3, 0 ]
        } ]
  });
});
