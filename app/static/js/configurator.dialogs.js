// ****************************************
// BANKPERSO DIALOGS: /bankperso.dialogs.js
// ----------------------------------------
// Version: 1.0
// Date: 20-10-2022

var screen_size = [$_width('screen-max'), $_height('screen-max')];

// ===========================
// Dialog windows declarations
// ===========================

var $ConfiguratorSubmitDialog = {
    base         : $BaseDialog,

    // ================================
    // Configurator Submit Dialog Class
    // ================================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    action       : null,
    command      : null,
    group        : null,
    mode         : null,
    id           : null,
    current      : null,
    keys         : [],

    is_error     : false,

    init: function() {
        this.container = $("#"+this.id+"-confirm-container");
    },

    callback: function() {
        return this.base.callback();
    },

    is_focused: function() {
        return this.base.is_focused();
    },

    activate: function(group) {
        this.current = tablines[group].get_current();
        if (is_null(this.current))
            return;

        this.group = group;
        this.id = this.current.attr('id');

        if (this.id == selector.row_id)
            return;

        if (this.IsDebug)
            alert('$ConfiguratorSubmitDialog.activate:'+group+':'+this.id);

        $Go(default_log_action);
    },

    open: function(mode) {
        this.setDefaultSize();
    },

    setDefaultSize: function() {
    },

    submit: function() {
        $onParentFormSubmit();
    },

    verified: function() {
        this.confirmed();
    },

    confirmed: function() {
        var self = $ConfiguratorSubmitDialog;
        var params = null;
        
        var is_run = true;

        switch (this.command) {
            case 'create':
            case 'update':
                break;
            default:
                is_run = false;
                break;
        }

        if (is_run) {
            $("#command", this.box).each(function(index) {
                var ob = $(this);
                if (is_exist(ob)) {
                    ob.val(self.command);
                }
            });
            this.submit(params);
            this.setDefaultSize('clean');
        }

        //this.base.close();
    },

    cancel: function() {
        this.base.close();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{

    // ------------------------------
    // Configurator Page Form Dialogs
    // ------------------------------

    $("#config-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:180, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $ConfiguratorSubmitDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $ConfiguratorSubmitDialog.cancel(); }}
        ],
        modal: true,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
        close: function() {
            $BaseDialog.onClose();
        }
    });
});
