// ***************************************************
// APPLICATION PAGE DECLARATION: /admin.default.js
// HELPER FUNCTION CONTROLS MANAGER
// ---------------------------------------------------
// Version: 2.00
// Date: 20-10-2022

// =======================
// Component control class
// =======================

var $LocalPageScroller = {
    page      : { 'base':null, 'top':0, 'height':0 },
    control   : { 'ob':null, 'default_position':0, 'top':0, 'height':0, 'isDefault':0, 'isMoved':0, 'isShouldBeMoved':0 },
    position  : 0,
    is_trace  : 0,

    init: function() {
    },

    reset: function(force) {
    },

    trace: function(force) {
    },

    checkPosition: function(reset) {
    },

    move: function() {
    }
};

var $PageController = {
    callbacks : null,
    is_trace  : 0,

    init: function() {
    },

    reset: function(force) {
    },

    trace: function(force) {
    },

    default_action: function(action, args) {
        //
        // Should return current_action value
        //
        if (action == default_action) {
            args['user_id'] = SelectedGetItem(LINE, 'id');
            return '000';
        }
    },

    action: function(action, args) {
        if (action > default_action) {
            var user_id = SelectedGetItem(LINE, 'id');

            if (is_null(user_id))
                return;
            
            ObjectUpdate(args, {
                'action'     : action,
                'user_id'    : user_id,
            });
        }
    },

    setTable: function(callbacks, action) {
        this.callbacks = callbacks;
        mid = '';
        //
        //
        //
        //set_table = this.callbacks['set_table'];
        /*
        switch (action) {
            case '100':
        }
        */
        return mid;
    },

    move: function() {
    }
};

var $PageLoader = {
    container   : null,
    actions     : {'change':'502'},

    IsDebug : 0, IsDeepDebug : 0, IsTrace : 0, IsLog : 0,

    action      : null,
    id          : null,
    command     : '',
    mode        : '',
    box         : null,
    
    scroll_mode : '',
    scroll_top  : 0,
    top         : 0,
    height      : 0,

    is_error    : false,
    is_shown    : false,
    is_locked   : false,

    line        : {'id' : null, 'state_is_open' : -1},

    init: function() {
        this.container = $("#"+selected_review_id);

        if (this.IsTrace)
            alert('references.$PageLoader.init:'+$LineSelector.get_id()+':'+$LineSelector.get_current().get(0).outerHTML);

        this.line['id'] = null;

        is_full_container = 1;

        this.scroll_top = $(window).scrollTop();
    },

    reset: function() {
        this._show();
        this._reset();

        this.scroll_top = $(window).scrollTop();
    },

    scroll: function() {
    },

    remove_current: function() {
    },

    _lock: function() {
        this.is_locked = true;
    },

    _unlock: function() {
        this.is_locked = false;
    },

    locked: function() {
        return false;
    },

    _before: function(ob, command) {
    },

    _reset: function() {
        this.action = null;
        this.id = null;
        this.mode = '';
        this.box = null;
    },

    _hide: function() {
        if (is_empty(this.mode))
            return;

        var key = this.mode.toUpperCase();

        this.is_shown = true;
    },

    _show: function() {
        if (is_empty(this.mode))
            return;

        var key = this.mode.toUpperCase();

        this.is_shown = false;
    },

    _clean: function() {
    },

    set: function(x) {
    },

    get: function(action, ob, command) {
    },

    cancel: function(action, ob, command) {
        this._clean();
        this._show();
        this._after();
    },

    check: function(x) {
    },

    check_reference: function(x) {
    },

    check_paid: function(info) {
    },

    check_refers: function(info) {
    },

    check_images: function(currentfile) {
    },

    set_status: function(status) {
    },

    set_barcode: function(props) {
    },

    update_param_combo: function(x) {
    },

    handle: function(x) {
        this._reset();
        this._after();
    },

    handle_change: function(ob, command) {
    },

    handle_refresh: function(action, ob, command) {
    },

    select_item: function(action, ob, command) {
    },

    disable_edit: function(props) {
    },

    disable_review: function(props) {
    },

    disable_statuses: function(props) {
    },

    _register: function() {
    },

    is_activated: function() {
        return false;
    },

    activate: function(ob) {
    },

    refresh_line: function(response, line) {
    },

    refresh_status: function(response) {
    },

    refresh_after_review: function(response) {
    },

    refresh: function(response) {
    },

    _after: function() {
        selected_menu_action = default_log_action;
        isCallback = false;
    }
};
