import { Card, CardBody } from "@nextui-org/react";

interface PerkProps {
  icon?: React.JSX.Element;
  title?: string;
  description: string;
}

const Perk: React.FC<PerkProps> = ({ icon, title, description }) => {
  return (
    <Card className="md:w-1/4 p-4" isHoverable={true}>
      <CardBody className="flex flex-col gap-2 justify-center items-center">
        {icon}
        <h3 className="text-xl text-center font-extrabold capitalize text-deepindigo">
          {title}
        </h3>
        <p>{description}</p>
      </CardBody>
    </Card>
  );
};

export default Perk;
