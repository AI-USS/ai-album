var NameWidget = function(args) {

    // 1. Find a current color setting in the annotation, if any
    var currentNameBody = args.annotation ? 
      args.annotation.bodies.find(function(b) {
        return b.purpose == 'name';
      }) : null;
    
    // 2. Keep the value in a variable
    var currentNameValue = currentNameBody ? currentNameBody.value : null;
    
    // 3. Triggers callbacks on user action
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
    
    // 4. This part renders the UI elements
    var createTextArea = function(value) {
      var textArea = document.createElement('textarea');
    
      if (currentNameValue)
        textArea.defaultValue = currentNameValue
    
      textArea.placeholder = "Imię"
      textArea.className = 'name';
      textArea.type = "text"
      textArea.addEventListener('change', addTag)
    //   button.placeholder = "Imię"
     
      return textArea;
    }
    
    var container = document.createElement('div');
    container.className = 'colorselector-widget';
    
    var name = createTextArea('name');
    
    
    container.appendChild(name);
    
    
    return container;
    }



    var LastNameWidget = function(args) {

        // 1. Find a current color setting in the annotation, if any
        var currentLastNameBody = args.annotation ? 
          args.annotation.bodies.find(function(b) {
            return b.purpose == 'lastName';
          }) : null;
        
        // 2. Keep the value in a variable
        var currentLastNameValue = currentLastNameBody ? currentLastNameBody.value : null;
        
        // 3. Triggers callbacks on user action
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
        
        // 4. This part renders the UI elements
        var createTextArea = function(value) {
          var textArea = document.createElement('textarea');
        
          if (currentLastNameValue)
            textArea.defaultValue = currentLastNameValue
        
          textArea.placeholder = "Nazwisko"
          textArea.className = 'lastName';
          textArea.type = "text"
          textArea.addEventListener('change', addTag)
        //   button.placeholder = "Imię"
         
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

          // 1. Find a current checkbox setting in the annotation, if any
          var currentCheckboxBody = args.annotation ? 
            args.annotation.bodies.find(function(b) {
              return b.purpose == 'newPerson';
            }) : null;
        
          // 2. Keep the value in a variable (default is false)
          var currentCheckboxValue = currentCheckboxBody ? currentCheckboxBody.value : false;
        
          // 3. Triggers callbacks on user action
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
        
          // 4. This part renders the UI elements
          var createCheckbox = function(isChecked) {
            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = isChecked;
            checkbox.className = 'checkbox-widget';
            checkbox.addEventListener('change', toggleCheckbox);
        
            return checkbox;
          }
        
          // Create container for the widget
          var container = document.createElement('div');
          container.className = 'checkbox-widget-container';

          var label = document.createElement('label');
          label.textContent = " Czy dodać jako nową osobę?";
          label.className = 'checkbox-label';
          // Create checkbox input
          var checkbox = createCheckbox(currentCheckboxValue);
        
          // Append the checkbox to the container
          container.appendChild(checkbox);
          container.appendChild(label);

        
          return container;
        }