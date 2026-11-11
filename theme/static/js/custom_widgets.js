var PersonWidget = function(args) {
    const values = Object.fromEntries((args.annotation?.bodies || []).map(body => [body.purpose, body.value]));
    return createPersonPicker(values, next => {
        args.onBatchModify(labelBodies(next).map(body => ({action: 'upsert', body})), true);
    });
};

var NameAndLastNameFormatter = function(annotation) {
    const values = Object.fromEntries(annotation.bodies.map(body => [body.purpose, body.value]));
    return {'style': `stroke-width:3; stroke:${values.name && values.lastName ? '#087f72' : '#b8600a'}`};
};
