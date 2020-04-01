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
        }
    });
});
