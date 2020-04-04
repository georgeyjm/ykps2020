let dataAppended = false;

$('#anonymity-modal').on('show.bs.modal', () => {
    if (dataAppended) return;
    $.get('/static/misc/anonymity.html', resp => {
        $('#anonymity-modal .modal-body').append(resp);
        dataAppended = true;
    });
});
