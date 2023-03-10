// ******************************
// MAIN DIALOGS: /main.dialogs.js
// ------------------------------
// Version: 1.0
// Date: 20-10-2022

var screen_size = [$_width('screen-max'), $_height('screen-max')];

// ===========================
// Dialog windows declarations
// ===========================

var $MainSubmitDialog = {
    base         : $BaseDialog,

    // =============================
    // Main Submit Dialog Class
    // =============================

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

    get_row_item: function(key) {
        return $(".log-"+key, this.current);
    },

    get_form_item: function(key) {
        return $("#"+this.mode+"_"+key, this.box);
    },

    set_data: function(key, default_value) {
    },

    get_data: function(key, default_value) {
    },

    clean_data: function(key, value) {
    },

    disable: function(key) {
    },

    enable: function(key) {
    },

    set: function(x) {
    },

    activate: function(group) {
        this.current = tablines[group].get_current();
        this.group = group;

        if (this.IsDebug)
            alert('$MainSubmitDialog.activate:'+group+':'+this.current.attr('id'));

        switch (group) {
            case 'activities':
                break;
            case 'reliabilities':
                break;
        }
    },

    open: function(action) {
        this.id = this.mode;

        this.init();

        this.setDefaultSize();
    },

    setDefaultSize: function(command) {
        var self = $MainSubmitDialog;
        this.box = $("#"+this.mode+"-box");

        if (is_empty(command))
            command = this.command;

        var is_open = true;

        switch (this.mode) {
            case 'reliability':
                break;
            case 'activity':
                break;
        }

        if (is_open) 
            this.base.open(this.id);
    },

    submit: function(params) {
    },

    confirmed: function() {
    },

    cancel: function() {
        this.close();
    },

    close: function() {
        $onCloseDialog(null);
        this.base.close();
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{

    // ---------------------------------
    // Refer Create/Change/Remove Dialog
    // ---------------------------------

    $("#activity-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:452, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $MainSubmitDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $MainSubmitDialog.cancel(); }}
        ],
        modal: false,
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

    $("#reliability-confirm-container").dialog({
        autoOpen: false,
        width:540,
        height:260,
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $MainSubmitDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $MainSubmitDialog.cancel(); }}
        ],
        modal: false,
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
