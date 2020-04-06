$('#delete-message-confirm-modal').on('show.bs.modal', function(event) {
    let messageData = $(event.relatedTarget).parent();
    let messageId = messageData.data('message-id');
    let messageRecipient = messageData.data('message-recipient');
    let modal = $(this);
    modal.find('.modal-body').html(`Are you sure you want to delete the message for <strong>${messageRecipient}</strong>? You can&rsquo;t undo this action.`);
    modal.find('#confirm-delete-message-button').data('message-id', messageId);
});

$('#confirm-delete-message-button').click(() => {
    let messageId = $('#confirm-delete-message-button').data('message-id');
    $.post('/message/delete', { id: messageId }, resp => {
        if (resp.code === 0) {
            // Hide popup modal
            $('#delete-message-confirm-modal').modal('hide');
            // Delete corresponding card element
            $(`.card-links-container[data-message-id=${messageId}]`).parent().parent().remove();
            // Append message if no messages left
            if ($('.message').length === 0) {
                $('.main-content-container').find('div.mt-5').remove();
                $('.main-content-container').append(`
                  <div class='col-12 col-md-10 col-lg-8 col-xl-6 mt-4 p-0'>
                    <p class='text-muted'>You haven&rsquo;t drafted any message yet! Click the <strong>&ldquo;Draft New Message&rdquo;</strong> button above to start drafting a message to someone.</p>
                  </div>
                `);
            }
        }
    });
});

$('[data-toggle="tooltip"]').tooltip();
  