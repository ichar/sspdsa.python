
// ******************************************
// REFERENCES DIALOGS: /reference.dialogs.js
// ------------------------------------------
// Version: 1.0
// Date: 20-10-2022

var screen_size = [$_width('screen-max'), $_height('screen-max')];

// ===========================
// Dialog windows declarations
// ===========================

var $ReferenceSubmitDialog = {
    base         : $BaseDialog,

    // =============================
    // Reference Submit Dialog Class
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
        var value = this.get_row_item(key).html();

        switch (key) {
        case 'ip':
            var k, v;
            var values = value.indexOf('.') > -1 ? value.split('.') : ['']*4;
            for (var n=0; n<4; n++) {
                k = key+'_p'+(n+1);
                v = values[n];
                //alert(v+':'+k+':'+n);
                this.get_form_item(k).val(v);
            }
            break;
        case 'state':
            var id = this.mode+"_state";
            var ob = $("input[name="+id+"]", this.box);
            var v = value == 'Да' ? 1 : 0;
            ob.val(v);
            if (v == 0) 
                $("#"+id+"_1").prop('checked', 1);
            else if (v > 0) 
                $("#"+id+"_2").prop('checked', 1);
            break;
        case 'priority':
            var ob = $("input[name="+id+"]", this.box);
            ob.val(value);
            var obv = $("#"+id+"_value", this.box);
            obv.html(value);
            //alert('set_data'+':'+ob.val()+':'+id);
        default:
            this.get_form_item(key).val(value);
        }

        if (this.IsDebug)
            alert('$ReferenceSubmitDialog.set_data:'+key+':'+value);
    },

    get_data: function(key, default_value) {
        value = null;

        switch (key) {
        case 'ip':
            var k;
            var values = [];
            value = '';
            for (var n=0; n<4; n++) {
                k = key+'_p'+(n+1);
                values.push(this.get_form_item(k).val() || '');
            }
            value = values.join('.');
            break;
        case 'state':
            var id = this.mode+"_state";
            var ob = $("input[name="+id+"]", this.box);
            value = $("#"+id+"_2").prop('checked') ? 1 : 0;
            //alert(ob.val()+':'+value);
            break;
        case 'priority':
            var id = this.mode+"_priority";
            var ob = $("input[name="+id+"]", this.box);
            value = ob.val();
            //alert('get_data'+':'+ob.val()+':'+id);
            break;
        default:
            value = this.get_form_item(key).val() || default_value;
        }

        if (this.IsDebug)
            alert('$ReferenceSubmitDialog.get_data:'+key+':'+value);

        return value;
    },

    clean_data: function(key, value) {
        switch (key) {
        case 'ip':
            var k, v;
            var values = value.indexOf('.') > -1 ? value.split('.') : ['']*4;
            for (var n=0; n<4; n++) {
                k = key+'_p'+(n+1);
                v = values[n] || '';
                //alert(v+':'+k+':'+n);
                this.get_form_item(k).val(v);
            }
            break;
        case 'state':
            var id = this.mode+"_state";
            var ob = $("input[name="+id+"]", this.box);
            ob.val(0);
            $("#"+id+"_2").prop('checked', 0);
            $("#"+id+"_1").prop('checked', 1);
            break;
        default:
            this.get_form_item(key).val(value);
        }
    },

    disable: function(key) {
        this.get_form_item(key).prop("disabled", true).addClass('disabled');
    },

    enable: function(key) {
        this.get_form_item(key).prop("disabled", false).removeClass('disabled');
    },

    set: function(x) {
        var data = getattr(x, 'data', null);
        var mode = getattr(data, 'mode', null);
        var id = getattr(data, 'id', null);
        var pk = getattr(data, 'pk', null);

        if (this.IsLog)
            console.log('$ReferenceSubmitDialog.set:', mode, pk, data);

        switch (mode) {
            case 'messagetype':
                this.box = $("#"+mode+"-box");
                this.get_form_item(id).val(pk);
        }

        this.base.open(this.id);
    },

    activate: function(group) {
        this.current = tablines[group].get_current();
        this.group = group;

        if (this.IsDebug)
            alert('$ReferenceSubmitDialog.activate:'+group+':'+this.current.attr('id'));

        switch (group) {
            case 'messagetypes':
                $("#action-node_change").prop("disabled", true).addClass('disabled');
                $("#action-messagetype_add").prop("disabled", false).removeClass('disabled');
                $("#action-messagetype_change").prop("disabled", false).removeClass('disabled');
                $("#action-bind_send").prop("disabled", true).addClass('disabled');
                break;
            case 'nodes':
                $("#action-node_change").prop("disabled", false).removeClass('disabled');
                $("#action-messagetype_add").prop("disabled", true).addClass('disabled');
                $("#action-messagetype_change").prop("disabled", true).addClass('disabled');
                $("#action-bind_send").prop("disabled", true).addClass('disabled');
                break;
            case 'binds':
                $("#action-node_change").prop("disabled", true).addClass('disabled');
                $("#action-messagetype_add").prop("disabled", true).addClass('disabled');
                $("#action-messagetype_change").prop("disabled", true).addClass('disabled');
                $("#action-bind_send").prop("disabled", false).removeClass('disabled');
                break;
            case 'divisions':
                $("#action-node_change").prop("disabled", true).addClass('disabled');
                $("#action-messagetype_add").prop("disabled", true).addClass('disabled');
                $("#action-messagetype_change").prop("disabled", true).addClass('disabled');
                $("#action-bind_send").prop("disabled", true).addClass('disabled');
        }
    },

    open: function(action) {
        if (this.base.opened)
            return;

        this.is_error = false;
        this.action = action;

        switch (this.action) {
            case 'node_change':
                this.command = 'update';
                this.mode = 'node';
                break;
            case 'messagetype_add':
                this.command = 'create';
                this.mode = 'messagetype';
                break;
            case 'messagetype_change':
                this.command = 'update';
                this.mode = 'messagetype';
                break;
            case 'bind_send':
                this.command = 'send';
                this.mode = 'bind';
                break;
        }

        this.id = this.mode;

        this.init();

        this.setDefaultSize();
    },

    setDefaultSize: function(command) {
        var self = $ReferenceSubmitDialog;
        this.box = $("#"+this.mode+"-box");

        if (is_empty(command))
            command = this.command;

        var is_open = true;

        switch (this.mode) {
            case 'messagetype':
                this.keys = ['id', 'name', 'priority'];
                if (command == 'update') {
                    this.keys.forEach(function(key, index) {
                        self.set_data(key, ['id', 'priority'].indexOf(key) > -1 ? 0 : '');
                    });
                    self.disable('id');
                    //self.disable('name');
                } else {
                    this.keys.forEach(function(key, index) {
                        self.clean_data(key, ['priority'].indexOf(key) > -1 ? 0 : '');
                    });

                    is_open = false;

                    var params = { 'mode':this.mode, 'command':this.command, 'id':'id' };

                    if (this.IsDebug)
                        alert(reprObject(params));

                    $Handle('502', function(x) { $ReferenceSubmitDialog.set(x); }, params);
                }
                break;
            case 'node':
                this.keys = ['id', 'ndiv', 'name', 'fullname', 'ip', 'port1', 'port2', 'state'];
                if (command == 'update') {
                    this.keys.forEach(function(key, index) {
                        self.set_data(key, ['id', 'ndiv', 'state'].indexOf(key) > -1 ? 0 : '');
                    });
                    self.disable('id');
                    self.disable('ndiv');
                    self.disable('name');
                    self.disable('fullname');
                    //var state = this.get_form_item('state');
                    //$("option", state)[0].prop("selected", true);
                    //state.prop("selectedIndex", 0);
                } else {
                    this.keys.forEach(function(key, index) {
                        self.clean_data(key, ['ndiv', 'state'].indexOf(key) > -1 ? 0 : '');
                    });
                }
                break;
            case 'bind':
                this.container.dialog("option", "height", 482);
        }

        if (is_open) 
            this.base.open(this.id);
    },

    submit: function(params) {
        isCallback = true;

        if (this.IsDebug)
            alert('submit:'+ reprObject(params));

        $Handle('503', null, params);
        //$onParentFormSubmit();
    },

    confirmed: function() {
        var self = $ReferenceSubmitDialog;
        var params = null;
        
        var is_run = true;

        switch (this.command) {
            case 'create':
            case 'update':
                params = { 'mode':this.mode, 'command':this.command, 'row_id': selector.id, 'group': selector.group };
                if (this.mode == 'messagetype') {
                    this.keys.forEach(function(key, index) {
                        params[key] = self.get_data(key, key == 'priority' ? 0 : '');
                    });
                } if (this.mode == 'node') {
                    this.keys.forEach(function(key, index) {
                        params[key] = self.get_data(key, key == 'state' ? 0 : '');
                    });
                } else if (this.mode == 'bind') {
                    alert('bind confirmed');
                    is_run = false;
                }
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
            //this.setDefaultSize('clean');
        }

        //this.base.close();
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

    $("#division-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:160, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $ReferenceSubmitDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $ReferenceSubmitDialog.cancel(); }}
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

    $("#messagetype-confirm-container").dialog({
        autoOpen: false,
        width:540,
        height:260,
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $ReferenceSubmitDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $ReferenceSubmitDialog.cancel(); }}
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

    $("#node-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:452, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $ReferenceSubmitDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $ReferenceSubmitDialog.cancel(); }}
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

    $("#bind-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:400, // 136
        position:0,
        buttons: [
            //{text: keywords['Confirm'], click: function() { $ReferenceSubmitDialog.confirmed(); }},
            {text: keywords['Close'],  click: function() { $ReferenceSubmitDialog.cancel(); }}
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
