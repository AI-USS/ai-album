var NameWidget = function(args) {

    var currentNameBody = args.annotation ? 
      args.annotation.bodies.find(function(b) {
        return b.purpose == 'name';
      }) : null;
    
    var currentNameValue = currentNameBody ? currentNameBody.value : null;
    
    var addTag = function(evt) {
      if (currentNameBody) {
        args.onUpdateBody(currentNameBody, {
          type: 'TextualBody',
          purpose: 'name',
          value: evt.target.value
        });
      } else { 
        args.onAppendBody({
          type: 'TextualBody',
          purpose: 'name',
          value: evt.target.value
        });
      }
    }
    
    var createTextArea = function(value) {
      var textArea = document.createElement('textarea');
    
      if (currentNameValue)
        textArea.defaultValue = currentNameValue
    
      textArea.placeholder = "Imię"
      textArea.className = 'name';
      textArea.type = "text"
      textArea.addEventListener('change', addTag)
     
      return textArea;
    }
    
    var container = document.createElement('div');
    container.className = 'colorselector-widget';
    
    var name = createTextArea('name');
    
    
    container.appendChild(name);
    
    
    return container;
    }



    var LastNameWidget = function(args) {

        var currentLastNameBody = args.annotation ? 
          args.annotation.bodies.find(function(b) {
            return b.purpose == 'lastName';
          }) : null;
        
        var currentLastNameValue = currentLastNameBody ? currentLastNameBody.value : null;
        
        var addTag = function(evt) {
          if (currentLastNameBody) {
            args.onUpdateBody(currentLastNameBody, {
              type: 'TextualBody',
              purpose: 'lastName',
              value: evt.target.value
            });
          } else { 
            args.onAppendBody({
              type: 'TextualBody',
              purpose: 'lastName',
              value: evt.target.value
            });
          }
        }
        
        var createTextArea = function(value) {
          var textArea = document.createElement('textarea');
        
          if (currentLastNameValue)
            textArea.defaultValue = currentLastNameValue
        
          textArea.placeholder = "Nazwisko"
          textArea.className = 'lastName';
          textArea.type = "text"
          textArea.addEventListener('change', addTag)
         
          return textArea;
        }
        
        var container = document.createElement('div');
        container.className = 'colorselector-widget';
        
        var lastName = createTextArea('lastName');
        
        
        container.appendChild(lastName);
        
        
        return container;
        }
        


        var NameAndLastNameFormatter = function(annotation) {
          const isNotLastName = annotation.bodies.find(b => {
            return b.purpose === 'lastName' && b.value === null || b.purpose === 'lastName' && b.value === ""
          })
          const isNotName = annotation.bodies.find(b => {
            return b.purpose === 'name' && b.value === null || b.purpose === 'name' && b.value === ""
          });
          if (isNotLastName || isNotName) {
            return {
              'style': 'stroke-width:4; stroke: red'
            }
          } else {
            return {
              'style': 'stroke-width:4; stroke: green'
            }
          }
        }


        var NewPersonWidget = function(args) {

          var currentCheckboxBody = args.annotation ? 
            args.annotation.bodies.find(function(b) {
              return b.purpose == 'newPerson';
            }) : null;
        
          var currentCheckboxValue = currentCheckboxBody ? currentCheckboxBody.value : false;
        
          var toggleCheckbox = function(evt) {
            if (currentCheckboxBody) {
              args.onUpdateBody(currentCheckboxBody, {
                type: 'TextualBody',
                purpose: 'newPerson',
                value: evt.target.checked
              });
            } else { 
              args.onAppendBody({
                type: 'TextualBody',
                purpose: 'newPerson',
                value: evt.target.checked
              });
            }
          }
        
          var createCheckbox = function(isChecked) {
            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = isChecked;
            checkbox.className = 'checkbox-widget';
            checkbox.addEventListener('change', toggleCheckbox);
        
            return checkbox;
          }
        
          var container = document.createElement('div');
          container.className = 'checkbox-widget-container';

          var label = document.createElement('label');
          label.textContent = " Czy dodać jako nową osobę?";
          label.className = 'checkbox-label';
          var checkbox = createCheckbox(currentCheckboxValue);
        
          container.appendChild(checkbox);
          container.appendChild(label);

        
          return container;
        }
