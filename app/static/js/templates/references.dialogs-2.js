// ******************************************
// REFERENCES DIALOGS: /reference.dialogs.js
// ------------------------------------------
// Version: 1.0
// Date: 20-10-2022

var STATUS = 'change-status';

var screen_size = [$_width('screen-max'), $_height('screen-max')];

// ===========================
// Dialog windows declarations
// ===========================

var $ReferenceDialog = {
    container    : null,
    box          : null,
    mode         : '',
    state        : new Object(),

    IsTrace      : 0,

    init: function(mode) {
        this.mode = mode
        this.container = $("#"+this.mode+"-confirm-container");
        this.box = $("#"+this.mode+"-request");
        this.state = new Object();
    },

    get_id: function() {
        return this.container.attr('id');
    },

    get_mode: function() {
        return this.container.attr('mode');
    },

    set_mode: function(mode) {
        this.container.attr('mode', mode);
    },

    submit: function() {
        $onParentFormSubmit();
    },

    toggle: function(ob) {
        this.state['mode'] = this.get_mode();
    },

    is_important: function(mode) {
        return ['create', 'delete'].indexOf(mode) > -1 ? true : false;
    },

    setContent: function(id, data) {
        var mode = this.get_mode();

        this.box.html(
            keywords['refer confirmation']+' '+keywords[mode+' selected file']+
            ' ID:'+id+'? '+
            (this.is_important(mode) ? keywords['Recovery is impossible!']+' ' : '')+
            keywords['please confirm']
        );
    },

    open: function(command) {
        this.init();

        var mode = (command == 'admin:create' ? 'create' : (command == 'admin:delete' ? 'delete' : command));
        var id = SelectedGetItem(LINE, 'id');

        if (this.IsTrace)
            alert('open:'+command+':'+id);

        if (id == null)
            return;

        this.set_mode(mode);
        this.setContent(id, null);

        this.toggle(null);

        this.container.dialog("open");
    },

    confirmed: function() {
        this.close();

        if (!('mode' in this.state))
            return;

        var mode = this.state['mode'];
        var id = SelectedGetItem(LINE, 'id');
        var command = 'admin:'+mode;

        $("input[name='file_id']").each(function() { $(this).val(id); });
        $("#command").val(command);

        this.submit();
    },

    close: function() {
        this.container.dialog("close");
    }
};

var $ReferenceSubmitDialog = {
    base         : $BaseDialog,

    // =============================
    // Reference Submit Dialog Class
    // =============================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    command      : null,
    id           : null,
    mode         : null,

    callback: function() {
        return this.base.callback();
    },

    is_focused: function() {
        return this.base.is_focused();
    },

    setDefaultSize: function() {
        this.base.open(this.id);

        switch (this.mode) {
            case 'changedate':
                // chain a few methods for the first datepicker, jQuery style!
                $datepicker.pikaday('show').pikaday('currentMonth');
                break;
        }
    },

    submit: function() {
        $onParentFormSubmit();
    },

    open: function(mode) {
        if (this.base.opened)
            return;

        this.mode = mode;

        switch (this.mode) {
            case 'tagsearch':
                this.command = 'admin:tagsearch';
                this.id = 'tagsearch';
                break;
        }

        this.setDefaultSize();
    },

    verified: function() {
        this.confirmed();
    },

    confirmed: function() {
        this.base.close();

        switch (this.mode) {
            case 'tagsearch':
                var value = $("#tagsearch-context").val();
                $("#specified").val(value);
                $("#command").val(this.command);
                break;
        }

        this.submit();
    },

    cancel: function() {
        this.base.close();
    }
};

var $ReferenceSelectorDialog = {
    base         : $BaseScreenDialog,

    // ========================
    // Reference Selector Class
    // ========================

    IsDebug : 0, IsTrace : 0, IsLog : 0,

    // ---------------------
    // Base class attributes
    // ---------------------

    // ID of base container
    id           : null,
    // Mode of screen available
    mode         : 'available',
    // Flag to use cache
    with_cache   : 0,
    // Flag to lock screen
    with_lock    : 0,

    check_limit_height  : 0,

    // ---------------
    // Form's controls 
    // ---------------

    form         : null,

    timeout      : 300,
    timer        : null,

    // ----------------
    // Local attributes
    // ----------------

    command      : null,
    oid          : null,
    data         : null,
    columns      : null,
    props        : null,

    disabled_form  : '', //' disabled',
    check_on_exit  : false,

    is_active    : false,
    is_open      : false,
    is_error     : false,

    // Flag: this is mobile frame
    is_mobile    : null,

    input_ids    : null,

    init: function(ob, id, title, css) {
        this.id = id;

        this.form = $("#"+this.id+"-form");

        this.base.init(ob, this.id, this);

        if (this.IsLog)
            console.log('$ReferenceSelectorDialog.init:', this.id, this.base.form.width(), this.base.form.height());

        if (!is_null(this.base.box) && !is_empty(css))
            this.base.box.removeClass('create'+this.id).removeClass('update'+this.id).addClass(css);

        if (!is_empty(title))
            this.base.container.dialog("option", "title", title);

        this.oid = $LineSelector.get_id();

        this.initState();
    },

    initState: function() {
        this.is_mobile = $_mobile();

        this.with_lock = this.is_mobile ? 1 : 0;
        this.disabled_form = this.is_mobile ? ' disabled' : '';

        //this.IsTrace = this.is_mobile ? 1 : 0;
    },

    is_focused: function() {
        return this.is_open;
    },

    term: function() {
        this.base.term();
        this.is_open = false;
    },

    reset: function() {
        this.base.reset(this.with_cache);
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

    set_disabled_form: function(disabled) {
        var ids = disabled ? [] : (!is_null(this.input_ids) ? this.input_ids.slice() : []);

        $(":input", this.form).each(function() {
            var ob = $(this);
            var id = ob.attr('id');

            if (disabled) {
                if (!ob.prop("disabled")) {
                    $(this).prop("disabled", true);
                    ids.push(id);
                }
            }
            else if (ids.indexOf(id) > -1) {
                $(this).prop("disabled", false);
            }
        });

        this.input_ids = ids.slice();
    },

    setDefaultSize: function() {
        var offset = {'H' : [210, 0, 0], 'W' : [65, 0, 0], 'init' : [0, 760-$_width(this.mode)]};

        if (this.IsTrace)
            alert('$ReferenceSelectorDialog.setDefaultSize');

        this.base.setDefaultSize(offset);

        if (this.disabled_form)
            this.set_disabled_form(true);

        $BaseDialog.open(this.id);
    },

    checked: function(response) {
        var data = getObjectValueByKey(response, 'data', null);
        var errors = getObjectValueByKey(response, 'errors', null);

        if (!is_empty(errors)) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
            this.is_error = true;
        }
        else {
            var id = getObjectValueByKey(data, 'action_id', '');
            var message = getObjectValueByKey(data, 'message', '');

            if (this.IsTrace)
                alert('action_id:['+id+']:'+message);

            if (!is_empty(id)) {
                $_set_body_value(this.id+'_id', id);

                confirm_action = this.id+'.checked';

                $NotificationDialog.open(message);
            }

            this.check_on_exit = true;
        }
    },

    enabled: function() {
        var self = $ReferenceSelectorDialog;

        if (this.IsDebug)
            alert('enabled');

        this.columns.forEach(function(name, index) {
            var control_id = self.id+'_'+name;
            var prop = self.props[name];
            var prop_type = prop['type'];
            var prop_disabled = prop['disabled'];
            var ob = $("#"+control_id, self.base.form);

            if (prop_disabled) {
                ob.prop("disabled", false);

                if (prop_type == 1) {
                    var new_ob = $("#new_"+control_id, self.base.form);
                    new_ob.prop("disabled", false);
                }
            }
        });
    },

    refreshed: function(x) {
        var self = $ReferenceSelectorDialog;

        if (this.IsDebug)
            alert('refreshed');

        this.data = x['data'];
        this.columns = x['columns'];
        this.props = x['props'];

        this.columns.forEach(function(name, index) {
            var control_id = self.id+'_'+name;
            var value = self.data[name];
            var prop = self.props[name];
            var prop_type = prop['type'];
            var prop_disabled = prop['disabled'];
            var ob = $("#"+control_id, self.base.form);

            if (self.IsLog)
                console.log(name, value, prop, is_exist(ob), prop_disabled);

            if (prop_type == 2)
                ob.prop("selectedIndex", value);
            else if (prop_type == 1) {
                var sob = $("#new_"+control_id, self.base.form);
                if (!is_null(sob))
                    sob.val('');
                ob.val(value);
            }
            else
                ob.val(value);

            ob.prop("disabled", prop_disabled);

            if (prop_type == 1) {
                var new_ob = $("#new_"+control_id, self.base.form);
                new_ob.prop("disabled", prop_disabled);
            }
        });

        this.open(this.command);
    },

    resize: function() {
        this.onResize();
    },

    open: function(command) {
        $("#command", this.base.form).val('admin:'+command);

        if (this.IsDebug)        
            alert('open:'+command);

        var cacheid = this.base.cacheid;
        var html = this.base.box.html().replace(this.id+'-form', cacheid); 

        this.base.load(html);

        this.setDefaultSize();

        this.is_open = true;
    },

    create: function(id) {
        this.command = 'create'+id;

        this.init(null, id, keywords['Title:Create form of']+getattr(form_caption, id, 'object'), this.command);

        var action = '843';
        var params = {'command':this.command};

        no_window_scroll = true;

        $Handle(action, function(x) { $ReferenceSelectorDialog.refreshed(x); }, params);
    },

    update: function(id) {
        this.command = 'update'+id;

        this.init(null, id, keywords['Title:Update form of']+getattr(form_caption, id, 'object'), this.command);

        var action = '843';
        var params = {'command':this.command, 'id':this.oid};

        if (is_empty(this.oid)) {
            alert('$ReferenceSelectorDialog.update, oid is empty!');
            return;
        }

        $Handle(action, function(x) { $ReferenceSelectorDialog.refreshed(x); }, params);
    },

    delete: function(id) {
        this.command = 'delete'+id;

        this.init(null, id);

        no_window_scroll = true;

        confirm_action = 'admin:delete'+id;

        $ConfirmDialog.open(
            keywords['Command:'+capitalize(current_context)+' '+capitalize(id)+' removing'] + 
            '<br><div class="removescenario">'+keywords['ID '+current_context+' '+id]+':&nbsp;<span>'+this.oid+'</span></div>', 
            500);
    },

    clone: function(id) {
        this.command = 'clone'+id;

        this.init(null, id, keywords['Title:Clone form of']+getattr(form_caption, id, 'object'), this.command);

        if (is_empty(this.oid)) {
            alert('$ReferenceSelectorDialog.clone, oid is empty!');
            return;
        }

        var action = '843';
        var params = {'command':this.command, 'id':this.oid};

        no_window_scroll = true;

        $Handle(action, function(x) { $ReferenceSelectorDialog.refreshed(x); }, params);
    },

    refreshItem: function(ob) {
        var oid = ob.attr('id');
        var params = null;
        var callback = null;

        switch (oid) {
            case 'order_seller':
                this.action = '855';
                var command = 'seller';
                params = {'command':command, 'id':ob.val()};
                confirm_action = command;
                callback = refresh_order_item;
                break;
        }

        if (!is_empty(this.action))
            $Handle(this.action, function(x) { callback(x); }, params);
    },

    confirmed: function() {
        var action = '864';
        var params = {'command':this.command, 'submit':1};

        $Handle(action, function(x) { $ReferenceSelectorDialog.checked(x); }, params);
    },

    validate: function() {
        var self = $ReferenceSelectorDialog;

        var action = '845';
        var is_limited_length = ['create'+this.id, 'clone'+this.id].indexOf(this.command) > -1 ? 1 : 0;
        var params = {'command':this.command, 'submit':1, 'is_limited_length':is_limited_length};

        this.columns.forEach(function(name, index) {
            var control_id = self.id+'_'+name;
            var ob = $("#"+control_id, self.base.form);

            if (!is_null(ob))
                params[control_id] = ob.val();

            var prop = self.props[name];
            var prop_type = prop['type'];

            if (prop_type == 1) {
                var new_id = 'new_'+control_id;
                var new_ob = $("#"+new_id, self.base.form);

                if (!is_null(new_ob))
                    params[new_id] = new_ob.val();
            }
        });

        $Handle(action, function(x) { $ReferenceSelectorDialog.checked(x); }, params);
    },

    onResize: function() {
        /*
        if (this.is_open && $_mobile()) {
            this.cancel();

            this.setDefaultSize();
        }
        */
    },

    onOpen: function() {
        var self = $ReferenceSelectorDialog;

        $BaseScreenDialog.onOpen();

        if (!this.is_active) {
            this.timer = setTimeout(function() { 
                self.set_disabled_form(false);
                window.clearTimeout(self.timer);
                self.timer = null; 
            }, this.timeout);
        }
    },

    onClose: function() {
        this.term();

        if (this.check_on_exit)
            this.exit();
    },

    cancel: function() {
        $BaseDialog.cancel();
    },

    exit: function() {
        if (this.command == 'update'+this.id)
            $ShowOnStartup();
        else
            $onRefreshClick();

        this.check_on_exit = false;
    }
};

// =======
// Dialogs
// =======

jQuery(function($) 
{

    // ---------------------------------
    // Refer Create/change/Remove Dialog
    // ---------------------------------

    $("#refer-confirm-container").dialog({
        autoOpen: false,
        width:540, // 640
        height:160, // 136
        position:0,
        buttons: [
            {text: keywords['Confirm'], click: function() { $ReferenceDialog.confirmed(); }},
            {text: keywords['Reject'],  click: function() { $ReferenceDialog.close(); }}
        ],
        modal: true,
        draggable: true,
        resizable: false,
        position: {my: "center center", at: "center center", of: window, collision: "none"},
        create: function (event, ui) {
            $(event.target).parent().css("position", "fixed");
        },
    });
});
