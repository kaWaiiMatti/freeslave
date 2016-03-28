$(document).ready(function() {

  $('.navbar-nav').on('click', 'li > a', null, function(event) {
    event.preventDefault();
    $('#content').children().hide();
    $('#content').children($(event.currentTarget).attr('href')).show();
  });
  $('.navbar-nav > li > a').first().click();

  //Set automatic update for task list
  /*setInterval(function(){
     updateTasks();
     updateNodes();
  }, 3000);*/
  updateTasks();
  updateNodes();

  $('#submit_new_node').click(function(){
    postNewNode();
  });

  $('#submit_md5hash').click(function(){
    postMd5HashTask();
  });
  
  $('#refresh_node_list').click(function(){
    updateNodes();
  });
  
  $('#refresh_task_list').click(function(){
    updateTasks();
  });

    $('#md5hashtable').on('click', 'tbody > tr > td:nth-child(4)', null, function() {
        deleteTask(this);
    });
});

function deleteTask(element) {
    var taskId = parseInt($(element).data('taskId'));

    $.ajax('/api/tasks/' + taskId, {
        method: 'DELETE',
        success: function(data, status, xhr) {
            if(xhr.status === 204) {
                console.log('Successfully deleted a task!');
                $(element).parent().remove();
            }
        }
    });
}

function postNewNode() {
  var data = {
    'register': true,
    'nodes': []
  };

  $.each($('[data-form="new_node"]'), function() {
    switch (this.type) {
      case 'number':
        data[$(this).data('value')] = parseInt($(this).val());
        break;
      default:
        data[$(this).data('value')] = $(this).val();
    }
  });

  $.ajax('/api/nodes', {
    method: 'POST',
    data: JSON.stringify(data),
    success: function() {
      console.log('Successfully registered a new node!');
    },
    error: function(){
      console.log('Failed to register node!');
    }
  });
  console.log(JSON.stringify(data));
}

function postMd5HashTask() {
  var data = {
    type: 'md5hashtask'
  };

  $.each($('[data-form="md5hash"]'), function() {
    switch (this.type) {
      case 'number':
        data[$(this).data('value')] = parseInt($(this).val());
        break;
      default:
        data[$(this).data('value')] = $(this).val();
    }
  });
  console.log(data);
  //TODO: get the new task is successful and add to list

	$.ajax('/api/tasks', {
    method: 'POST',
    data: JSON.stringify(data),
    success: function() {
      updateTasks();
    }
  });

}

function updateTasks() {
  $.ajax('/api/tasks', {
    success: function(xhr) {
    	$('#md5hashtable tr').has('td').remove();
    
      $.each(xhr, function(index, item) {
        //TODO: alter to change content, rather than clear list and refill?
        $('#md5hashtable').append($('<tr>')
        .append($('<td>', {text:item.target_hash}))
        .append($('<td>', {text:item.max_length}))
        .append($('<td>', {text:item.result}))
        .append($('<td>', {text:'X', 'data-task-id': item.task_id})));
      });
    }
  });
}

function updateNodes() {
  $.ajax('/api/nodes', {
    success: function(xhr) {
    	$('#nodestable tr').has('td').remove();
    	
      $.each(xhr, function(index, item) {
        //TODO: alter to change content, rather than clear list and refill?
        $('#nodestable').append($('<tr>')
        .append($('<td>', {text:item.ip}))
        .append($('<td>', {text:item.port}))
        .append($('<td>', {text:item.last_active})));
      });
    }
  });
}
