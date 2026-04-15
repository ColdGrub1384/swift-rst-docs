import MySwiftLibrary

/// Says hello to a ``MySwiftLibrary.Animal``.
///
/// - Parameters:
///     - animal: An animal to say hello to.
///
/// - Returns A hello text.
public func Hello(animal: Animal) -> String {
    return "Hello \(animal.name)"
}