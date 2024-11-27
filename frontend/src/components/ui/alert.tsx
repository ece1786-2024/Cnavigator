import React from "react";

export const Alert: React.FC<{ message: string; type?: "error" | "info" | "success" }> = ({
  message,
  type = "info",
}) => {
  const getTypeStyles = () => {
    switch (type) {
      case "error":
        return "bg-red-100 text-red-800";
      case "success":
        return "bg-green-100 text-green-800";
      default:
        return "bg-blue-100 text-blue-800";
    }
  };

  return (
    <div className={`rounded-md p-4 ${getTypeStyles()}`}>
      <span>{message}</span>
    </div>
  );
};

export const AlertDescription: React.FC<{ description: string }> = ({ description }) => {
  return <p className="text-sm text-gray-500">{description}</p>;
};
