$(document).ready(function() {

  $('.navbar-nav').on('click', 'li > a', null, function(event) {
    event.preventDefault();
    $('#content').children().hide();
    $('#content').children($(event.currentTarget).attr('href')).show();
  });
  $('.navbar-nav > li > a').first().click();

  //Set automatic update for task list
  setInterval(function(){
     updateTasks();
     updateNodes();
  }, 3000);
  updateTasks();

  $('#submit_md5hash').click(function(){
    postMd5HashTask();
  });
});

function postMd5HashTask() {
  var data = {
    type: 'md5hashtask'
  };
  $.each($('[data-form="md5hash"]'), function(index, item) {
    switch (this.type) {
      case 'number':
        data[$(this).data('value')] = $(this).val(); //TODO: parse int
        break;
      default:
        data[$(this).data('value')] = $(this).val();
    }
  });
  console.log(data);
  //TODO: do ajax post, get the new task is successful and add to list
}

function updateTasks() {
  $.ajax('/api/tasks', {
    success: function(xhr) {
      $.each(xhr, function(index, item) {
        //TODO: alter to change content, rather than clear list and refill?
        $('#tasks').children('tbody').children('tr').remove();
        $('#tasks').append($('<tr>')
        .append($('<td>', {text:item.target_hash}))
        .append($('<td>', {text:item.max_length}))
        .append($('<td>', {text:'result are not posted yet...'})));
      });
    }
  });
}

function updateNodes() {
  $.ajax('/api/nodes', {
    success: function(xhr) {
      $.each(xhr, function(index, item) {
        //TODO: alter to change content, rather than clear list and refill?
        $('#nodes').children('tbody').children('tr').remove();
        $('#nodes').append($('<tr>')
        .append($('<td>', {text:item.ip}))
        .append($('<td>', {text:item.port}))
        .append($('<td>', {text:item.last_active})));
      });
    }
  });
}
