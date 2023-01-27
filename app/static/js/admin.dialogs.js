// ********************************
// ADMIN DIALOGS: /admin.dialogs.js
// --------------------------------
// Version: 2.00
// Date: 20-10-2022

// ===========================
// Dialog windows declarations
// ===========================

var $AdminServiceDialog = {
    base         : $BaseScreenDialog,

    // =============================
    // Provision Order History Class
    // =============================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action       : '',
    command      : null,
    id           : null,
    params       : null,

    // Mode of screen available
    mode         : 'client',
    // Flag to lock screen
    with_lock    : 0,

    init: function(ob) {
        this.base.init(ob, this.id, this);
    },

    term: function() {
        this.base.term();

        this.action = '';
        this.command = null;
        this.id = null;
        this.params = null;
        
        selected_menu_action = '';
    },

    reset: function() {
        this.base.reset(true);
    },

    lock_scroll: function() {
        if (!this.with_lock)
            return;

        this.base.lock_scroll();
    },

    unlock_scroll: function() {
        if (!this.with_lock)
            return;

        this.base.unlock_scroll();
    },

    open: function(ob, mode) {
        if (this.IsTrace)
            alert('$AdminServiceDialog.open, mode:'+mode);

        switch (mode) {
            case 'message':
                this.command = 'EMAIL_MESSAGE';
                this.action = '103';
                this.id = 'message';
                break;
            default:
                return;
        }

        this.init(ob);

        $BaseDialog.open(this.id);
    },

    handle: function(x) {
        var self = $AdminServiceDialog;

        $BaseDialog.close();

        var errors = !is_null(x) ? x['errors'] : null;

        switch (self.id) {
            case 'message':
                message_sent(x, errors);
                break;
        }

        self.term();
    },

    validate: function() {
        switch (this.id) {
            case 'message':
                var item = $LineSelector.get_current();
                var is_everybody = $("#item-everybody").prop('checked');
                var is_with_signature = $("#item-with-signature").prop('checked');
                var is_with_greeting = $("#item-with-greeting").prop('checked');
                var is_self_email = $("#item-self-email").prop('checked');

                this.params = {
                    'command'        : this.command, 
                    'to_everybody'   : is_everybody ? 1 : 0,
                    'with_signature' : is_with_signature ? 1 : 0,
                    'with_greeting'  : is_with_greeting ? 1 : 0,
                    'self_email'     : is_self_email ? 1 : 0,
                    'user'           : item.attr('id')
                };

                this.params['ids'] = is_everybody ? $LineSelector.getSelectedItems(1) : null;

                this.params['subject'] = $("#subject").val();
                this.params['message'] = $("#message").val();
        }

        selected_menu_action = this.action;

        this.base.progress();

        $Handle(this.action, function(x) { $AdminServiceDialog.handle(x); }, this.params);
    },

    onClose: function() {
        this.term();
    },

    confirmed: function() {
        this.validate();
    },

    cancel: function() {
        $BaseDialog.cancel();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{
    // --------------------------
    // Admin Email Message Dialog
    // --------------------------

    $("#message-confirm-container").dialog({
        autoOpen: false,
        width:785,
        height:604,
        position:0,
        buttons: [
            {text: keywords['OK'],     click: function() { $AdminServiceDialog.confirmed(); }},
            {text: keywords['Cancel'], click: function() { $AdminServiceDialog.cancel(); }}
        ],
        modal: false,
        draggable: true,
        resizable: true,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });
});
